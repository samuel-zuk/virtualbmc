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

class VirtualBMCError(Exception):
    message = None

    def __init__(self, message=None, **kwargs):
        if self.message and kwargs:
            self.message = self.message % kwargs
        else:
            self.message = message

        super().__init__(self.message)

    def __repr__(self):
        return str(self.message)


class IronicError:
    pass


class LibvirtError:
    pass


class NotFound(VirtualBMCError):
    message = 'Virtual machine with name %(name)s not found'


class DomainAlreadyExists(VirtualBMCError, LibvirtError):
    message = 'Domain %(name)s already exists'


class DomainNotFound(VirtualBMCError, LibvirtError):
    message = 'No libvirt domain with matching name %(name)s was found'


class LibvirtConnectionOpenError(VirtualBMCError, LibvirtError):
    message = ('Fail to establish a connection with libvirt URI "%(uri)s". '
               'Error: %(error)s')


class DetachProcessError(VirtualBMCError):
    message = ('Error when forking (detaching) the VirtualBMC process '
               'from its parent and session. Error: %(error)s')


class NodeNotFound(VirtualBMCError, IronicError):
    message = 'No Ironic node with matching name %(name)s was found'
