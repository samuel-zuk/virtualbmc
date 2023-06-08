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

from oslo_config import cfg
from oslo_config import generator

from virtualbmc.cfg import CONF
from virtualbmc import exception


default_opts = [
    cfg.StrOpt('bmc_type', choices=('libvirt', 'ironic')),
    cfg.BoolOpt('enabled', default=False),
    cfg.IPOpt('host_address', default='127.0.0.1'),
    cfg.PortOpt('port', default=1623),
    cfg.StrOpt('username'),
    cfg.StrOpt('password', secret=CONF['show_passwords']),
]

libvirt_opts = [
    cfg.StrOpt('domain_name'),
    cfg.UriOpt('libvirt_uri', default='qemu://system'),
    cfg.StrOpt('sasl_username'),
    cfg.StrOpt('sasl_password', secret=CONF['show_passwords']),
]

ironic_opts = [
    cfg.StrOpt('node_name')
]


def read_config(name, config_dir):
    config_path = os.path.join(config_dir, name, 'config')
    try:
        config = cfg.ConfigOpts()
        config.register_opts(default_opts)
        if CONF['enable_libvirt']:
            config.register_opts(libvirt_opts, group='libvirt')
        if CONF['enable_ironic']:
            config.register_opts(ironic_opts, group='ironic')
        # config files are actually parsed when the ConfigOpts object is called
        config(default_config_files=(config_path,))
        return config
    except (cfg.ConfigFilesNotFoundError,
            cfg.ConfigFilesPermissionDeniedError):
        raise exception.NotFound(name=name)


def write_config(config, config_dir):
    # NOTE: this function is hacked together from pieces of oslo.config's
    # sample config file generator. i couldn't find any info on how to generate
    # a config file from a pre-existing ConfigOpts object; it appears to be
    # something the folks on the oslo.config dev team don't intend for you to
    # be able to do for whatever reason (not yet, at least). hence, the weird
    # pseudo-object thing and the use of interfaces that are only really
    # documented in the source code itself, which can be found at
    # https://opendev.org/openstack/oslo.config/src/branch/master/oslo_config/generator.py

    config_path = os.path.join(config_dir, config['name'], 'config')

    def Object(**kwargs):
        return type("Object", (), kwargs)

    formatter_conf = Object(output_file=config_path,
                            wrap_width=79,
                            minimal=True,
                            summarize=False,
                            format='ini')
    formatter = generator._OptFormatter(formatter_conf, config_path)

    generator._output_opts(formatter, 'DEFAULT', config['DEFAULT'])
    for g in sorted(config._groups.keys()):
        formatter.write('\n\n')
        generator._output_opts(formatter, g, config[g])
