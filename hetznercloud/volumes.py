from hetznercloud.actions import HetznerCloudAction
from hetznercloud.exceptions import HetznerInvalidArgumentException, HetznerActionException
from hetznercloud.shared import _get_results


class HetznerCloudVolumeAction(object):
    def __init__(self, config):
        self._config = config

    def create(self, size: int, name: str, location=None, automount=False, server=None, format_fs='ext4'):
        """

        :param size: Size of the volume in GB
        :param name: Name of the volume
        :param location: Location to create the volume in (can be omitted if server is specified)
        :param automount: Auto mount volume after attach. server must be provided.
        :param server: Server to which to attach the volume once it’s created
        :param format_fs: Format volume after creation. One of: xfs, ext4
        :return:
        """

        if location is None and server is None:
            raise HetznerInvalidArgumentException('location and server volume volume')
        body = {'size': size, 'name': name, }
        if automount:
            body['automount'] = automount
        if server:
            body['server'] = server
        if location:
            body['location'] = location
        if format_fs:
            body['format'] = format_fs
        status_code, results = _get_results(self._config, 'volumes', method='POST', body=body)
        if status_code != 201:
            raise HetznerActionException(results)
        return HetznerCloudVolume._load_from_json(self._config, results['volume'])

    def get_all(self):
        status_code, results = _get_results(self._config, 'volumes')
        if status_code != 200:
            raise HetznerActionException(results)
        for result in results['volumes']:
            yield HetznerCloudVolume._load_from_json(self._config, result)

    def get(self, volume_id: int):
        status_code, result = _get_results(self._config, 'volumes/%s' % volume_id)
        if status_code != 200:
            raise HetznerActionException(result)
        return HetznerCloudVolume._load_from_json(self._config, result['volume'])


class HetznerCloudVolume(object):
    def __init__(self, config):
        self._config = config
        self.id = 0
        self.created = ''
        self.name = ''
        self.server = 0
        self.location_id = 0
        self.size = 0
        self.linux_device = ''
        self.labels = {}
        self.status = ''
        self.protection = False

    def attach_to_server(self, server_id: int, automount=False):
        if not server_id:
            raise HetznerInvalidArgumentException('server_id')
        status_code, result = _get_results(
            self._config, 'volumes/%s/actions/attach' % self.id, method='POST',
            body={'server': server_id, 'automount': automount}
        )
        if status_code != 201:
            raise HetznerActionException(result)
        self.server = server_id
        return HetznerCloudAction._load_from_json(self._config, result['action'])

    def detach_from_server(self):
        status_code, result = _get_results(self._config, 'volumes/%s/actions/detach' % self.id, method='POST')
        if status_code != 201:
            raise HetznerActionException(result)
        self.server = 0
        return HetznerCloudAction._load_from_json(self._config, result['action'])

    def resize(self, new_size: int):
        status_code, result = _get_results(
            self._config, 'volumes/%s/actions/resize' % self.id, method='POST',
            body={'size': new_size}
        )
        if status_code != 201:
            raise HetznerActionException(result)
        self.size = new_size

    def change_volume_protection(self, protection=True):
        status_code, result = _get_results(
            self._config, 'volumes/%s/actions/change_protection' % self.id,
            method='POST', body={'delete': protection}
        )
        if status_code != 201:
            raise HetznerActionException(result)
        self.protection = protection
        return HetznerCloudAction._load_from_json(self._config, result['action'])

    def update_name(self, new_name: str):
        status_code, result = _get_results(
            self._config, "volumes/%s" % self.id, method="PUT",
            body={'name': new_name}
        )
        if status_code != 200:
            raise HetznerActionException(result)
        self.name = new_name

    def delete(self):
        status_code, result = _get_results(self._config, 'volumes/%s' % self.id, method='DELETE')
        if status_code != 204:
            raise HetznerActionException(result)

    @staticmethod
    def _load_from_json(config, json):
        volume = HetznerCloudVolume(config)
        volume.id = int(json['id'])
        volume.created = json['created']
        volume.name = json['name']
        volume.server = int(json['server']) if json['server'] is not None else 0
        volume.size = int(json['size'])
        volume.linux_device = json['linux_device']
        volume.location_id = int(json['location']['id'])
        volume.protection = json['protection']['delete']
        volume.status = bool(json['status'])
        return volume
