#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
from os import path

from oslo_config import cfg
from oslo_config import generator as gen

from virtualbmc.conf.bmc import default as conf_default
from virtualbmc.conf.bmc import ironic as conf_ironic
from virtualbmc.conf.bmc import libvirt as conf_libvirt
from virtualbmc.conf import CONF as APP_CONF
from virtualbmc import exception

BMC_TYPES = ('libvirt', 'ironic')
INTERNAL_OPTS = ('config_dir', 'config_file', 'config_source')


class BMCConfig(cfg.ConfigOpts):
    def __init__(self, bmc_type=None):
        super().__init__()
        self.name = None
        self.conf_dir = None
        self.conf_path = None
        self.bmc_type = bmc_type

        conf_default.register_opts(self)

    def _register_bmc_type(self, bmc_type=None):
        if bmc_type is None:
            bmc_type = self.bmc_type

        if bmc_type == 'libvirt':
            conf_libvirt.register_opts(self)
        elif bmc_type == 'ironic':
            conf_ironic.register_opts(self)

    def _set_from_kwargs(self, options, kwargs, group=None):
        """Sets options that were specified as kwargs for a given group."""
        for opt in options:
            # opt.dest is opt.name but with '-' replaced with '_'
            if opt.dest in kwargs.keys():
                self.set_override(opt.dest, kwargs[opt.dest], group)
                kwargs.pop(opt.dest)
        return kwargs

    def _prepare_config_files(self, create_files=True):
        if self.conf_dir and self.conf_path:
            return

        base_dir = APP_CONF['config_dir'][0]

        conf_root = path.expanduser(path.abspath(base_dir))
        conf_dir = path.join(conf_root, self.name)
        if not path.exists(conf_dir):
            if create_files:
                if not path.exists(conf_root):
                    os.mkdir(conf_root)
                os.mkdir(conf_dir)
            else:
                raise FileNotFoundError(conf_dir)
        elif not path.isdir(conf_dir):
            raise ValueError(f'{conf_dir} is not a directory')

        self.conf_dir = conf_dir

        conf_path = path.join(conf_dir, 'vbmc.conf')
        if not path.exists(conf_path):
            if create_files:
                # creates an empty file
                open(conf_path, 'w').close()
            else:
                raise FileNotFoundError(conf_path)
        elif not path.isfile(conf_path):
            raise ValueError(f'{conf_path} is not a file')

        self.conf_path = conf_path

    def new(self, bmc_type, name, **kwargs):
        if bmc_type not in BMC_TYPES:
            raise ValueError(f'Invalid vBMC type {bmc_type}')

        self.name = name
        self.bmc_type = bmc_type

        self.set_override('name', name)
        self.set_override('bmc_type', bmc_type)
        kwargs = self._set_from_kwargs(conf_default.default_opts, kwargs)

        self._register_bmc_type()
        if self.bmc_type == 'libvirt':
            self._set_from_kwargs(conf_libvirt.libvirt_opts,
                                  kwargs, group='libvirt')
        elif self.bmc_type == 'ironic':
            self._set_from_kwargs(conf_ironic.ironic_opts,
                                  kwargs, group='ironic')

    def load(self, name):
        self.name = name

        try:
            self._prepare_config_files(create_files=False)
        except Exception:
            raise exception.NotFound(name=name)

        self._namespace = cfg._Namespace(self)

        try:
            cfg.ConfigParser._parse_file(self.conf_path, self._namespace)
        except cfg.ConfigFileValueError as ex:
            raise ValueError(str(ex))

        self.bmc_type = self['bmc_type']
        self._register_bmc_type(self.bmc_type)

        self(args=(name,),
             project=self.name,
             prog='vbmc',
             default_config_files=(self.conf_path,),
             default_config_dirs=(self.conf_dir,),
             validate_default_values=True,
             use_env=False,)

    def write(self, output_file=None):
        # NOTE: this function is hacked together from pieces of oslo.config's
        # sample config file generator. i couldn't find any info on how to
        # generate a config file from a pre-existing ConfigOpts object; it
        # appears to be something the folks on the oslo.config dev team don't
        # intend for you to be able to do for whatever reason (not yet, at
        # least). hence the use of interfaces that are only really documented
        # in the source code itself, which can be found at
        # https://opendev.org/openstack/oslo.config/src/branch/master/oslo_config/generator.py
        self._prepare_config_files()

        if output_file is None:
            with open(self.conf_path, 'w') as conf_file:
                return self.write(conf_file)

        fmt = gen._OptFormatter(APP_CONF['formatter'], output_file)
        groups = {'DEFAULT': self,
                  self.bmc_type: self._groups.get(self.bmc_type)}

        for (group_name, group_obj) in groups.items():
            fmt.format_group(group_name)
            for (opt_name, opt) in group_obj._opts.items():
                if opt_name in INTERNAL_OPTS:
                    continue

                # the format() method of the formatter will output the default
                # value of whatever Opt object is passed to it, so we need to
                # set that equal to the Opt's actual value.
                opt = opt['opt']
                opt.default = self._get(
                    opt_name,
                    group=(None if group_name == 'DEFAULT' else group_obj)
                )
                try:
                    fmt.write('\n')
                    fmt.format(opt, group_name)
                except Exception as ex:
                    fmt.write(
                        '# Warning: Failed to format sample for %s\n'
                        '# %s\n' % (opt_name, str(ex))
                    )
            fmt.write('\n\n')

    def init_parser(self, prog='vbmc', version=None, usage=None,
                    description=None, epilog=None):
        # code lifted from ConfigOpts.__call__:
        # https://opendev.org/openstack/oslo.config/src/branch/master/oslo_config/cfg.py#L2097
        project = 'vbmc'
        use_env = False

        prog, default_config_files, default_config_dirs = self._pre_setup(
            project, prog, version, usage, description, epilog, (), ())

        self._setup(project, prog, version, usage, default_config_files,
                    default_config_dirs, use_env)

        for opt, group in self._all_cli_opts():
            opt._add_to_cli(self._oparser, group)

    def get_parser(self):
        if self._oparser is None:
            self.init_parser()
        return self._oparser

    def as_dict(self, flatten=False):
        # ! creates a new object !
        output_dict = dict(self)
        bmc_type = self['bmc_type']

        # remove the actual group objects
        for group in self._groups.keys():
            output_dict.pop(group, None)

        if bmc_type is not None:
            if flatten:
                output_dict = dict(output_dict, **self[bmc_type])
            else:
                output_dict[bmc_type] = dict(self[bmc_type])

        for opt in INTERNAL_OPTS:
            output_dict.pop(opt, None)

        return output_dict
