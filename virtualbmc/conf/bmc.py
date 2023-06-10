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

import pathlib

from oslo_config import cfg
from oslo_config import generator as gen

from virtualbmc.conf import CONF
from virtualbmc import log

LOG = log.get_logger()


class BMCConfig:
    BMC_TYPES = ('libvirt', 'ironic')
    INTERNAL_OPTS = ('config_dir', 'config_file', 'config_source')

    _DEFAULT_OPTS = [
        cfg.StrOpt('bmc_type', choices=BMC_TYPES),
        cfg.BoolOpt('enabled'),
        cfg.IPOpt('host_address'),
        cfg.PortOpt('port'),
        cfg.StrOpt('username'),
        cfg.StrOpt('password', secret=CONF['show_passwords']),
    ]

    _LIBVIRT_OPTS = [
        cfg.StrOpt('domain_name'),
        cfg.URIOpt('libvirt_uri'),
        cfg.StrOpt('sasl_username'),
        cfg.StrOpt('sasl_password', secret=CONF['show_passwords']),
    ]

    _IRONIC_OPTS = [
        cfg.StrOpt('node_uuid'),
    ]

    def __init__(self, name, conf_dir, bmc_type=None, enabled=False,
                 username=None, password=None, host_address='127.0.0.1',
                 port=1623, **kwargs):
        self.name = name
        self.bmc_type = bmc_type
        if self.bmc_type is not None and self.bmc_type not in self.BMC_TYPES:
            raise ValueError(f'Invalid vBMC type {self.bmc_type}')

        self.conf_dir = pathlib.Path(conf_dir).expanduser().absolute()
        if not self.conf_dir.exists():
            self.conf_dir.mkdir(parents=True)
        elif not self.conf_dir.is_dir():
            raise ValueError(f'{conf_dir} is not a directory')

        self.conf_file = self.conf_dir / 'vbmc.conf'
        if not self.conf_file.exists():
            self.conf_file.touch()

        self.CONF = cfg.ConfigOpts()

        default_opts = {
            'enabled': enabled, 'host_address': host_address, 'port': port,
            'username': username, 'password': password
        }
        if bmc_type is not None:
            default_opts['bmc_type'] = bmc_type

        self._default_opts = (
            self._set_defaults(self._DEFAULT_OPTS, **default_opts))
        self.CONF.register_opts(self._default_opts)

        if bmc_type is None:
            self._init_conf()
            self.bmc_type = self.CONF['bmc_type']
            kwargs.pop('bmc_type')

        kwargs = {k: v for k, v in kwargs if k not in default_opts}
        if self.bmc_type == 'libvirt':
            self._libvirt_opts = (
                self._set_defaults(self._LIBVIRT_OPTS, **kwargs))
            self.CONF.register_opts(self._libvirt_opts, group='libvirt')
        elif self.bmc_type == 'ironic':
            self._ironic_opts = (
                self._set_defaults(self._IRONIC_OPTS, **kwargs))
            self.CONF.register_opts(self._ironic_opts, group='ironic')

        self._init_conf()

    @staticmethod
    def _set_defaults(opts, **kwargs):
        opts = {opt.name: opt for opt in opts}
        valid_option_names = opts.keys()
        for (name, value) in kwargs:
            if name in valid_option_names:
                opts[name].default = value
            else:
                LOG.debug(f'BMCConfig._set_defaults: unknown option {name}')
        return list(opts.values())

    def _init_conf(self):
        self.CONF(
            args=(),
            project=self.name,
            prog='vbmc',
            default_config_files=(str(self.conf_file),),
            default_config_dirs=(str(self.conf_dir),),
            validate_default_values=True,
            use_env=False,
        )

    def as_dict(self):
        d = dict(self.CONF, **self.CONF[self.bmc_type])
        d.pop(self.bmc_type, None)
        for o in self.INTERNAL_OPTS:
            d.pop(o, None)
        return d

    def set(self, opt_name, value, group=None):
        self.CONF.set_override(opt_name, value, group)

    def write(self):
        # NOTE: this function is hacked together from pieces of oslo.config's
        # sample config file generator. i couldn't find any info on how to
        # generate a config file from a pre-existing ConfigOpts object; it
        # appears to be something the folks on the oslo.config dev team don't
        # intend for you to be able to do for whatever reason (not yet, at
        # least). hence, the weird callable dict and the use of interfaces that
        # are only really documented in the source code itself, which can be
        # found at
        # https://opendev.org/openstack/oslo.config/src/branch/master/oslo_config/generator.py
        class FormatterConfig(dict):
            def __getattr__(self, attr):
                return self[attr]

            def __setattr__(self, attr, val):
                self[attr] = val

        with open(self.conf_file, 'w') as conf_file:
            fmt_conf = FormatterConfig((
                ('output_file', conf_file),
                ('wrap_width', 79),
                ('minimal', True),
                ('summarize', False),
                ('format', 'ini'),
            ))
            fmt = gen._OptFormatter(fmt_conf, conf_file)
            groups = dict({'DEFAULT': self.CONF},
                          **dict(sorted(self.CONF._groups.items())))

            for (group_name, group_obj) in groups.items():
                fmt.format_group(group_name)
                for (opt_name, opt) in sorted(group_obj._opts.items()):
                    if opt_name in self.INTERNAL_OPTS:
                        continue

                    opt = opt['opt']
                    opt.default = self.CONF._get(
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
