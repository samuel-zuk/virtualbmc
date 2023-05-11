==========
VirtualBMC
==========

Overview
--------

This repository is a development fork of https://opendev.org/openstack/virtualbmc,
intended to create a virtual BMC for Ironic nodes (instead of virtual machines).


Installation
~~~~~~~~~~~~

.. code-block:: bash

  git clone https://github.com/CCI-MOC/virtualbmc
  cd virtualbmc
  python setup.py install


Usage
~~~~~

Start the virtual BMC daemon. Note that this user must be able to run OpenStack commands
(for example, by sourcing an OpenStack RC file), and it must have permission to bind
ports.

.. code-block:: bash

  vbmcd

Once the daemon is running, you can create and start virtual BMC instances for a node
as follows:

.. code-block:: bash

  vbmc add <node name>
  vbmc start <node name>

Run `vbmc --help` to view additional options.


Supported IPMI commands
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

  # Power the virtual machine on, off, graceful off, NMI and reset
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on|off|soft|diag|reset

  # Check the power status
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status

  # Set the boot device to network, hd or cdrom
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootdev pxe|disk|cdrom

  # Get the current boot device
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootparam get 5
