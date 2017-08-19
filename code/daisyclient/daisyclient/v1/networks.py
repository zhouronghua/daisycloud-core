# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
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

import copy

from oslo_utils import encodeutils
from oslo_utils import strutils
import six
import six.moves.urllib.parse as urlparse

from daisyclient.common import utils
from daisyclient.openstack.common.apiclient import base

UPDATE_PARAMS = ('alias', 'mtu', 'vlan_id', 'ip', 'name', 'cluster_id',
                 'ip_ranges', 'vlan_start', 'vlan_end',
                 'gateway', 'cidr', 'description', 'type', 'ml2_type',
                 'network_type', 'physnet_name', 'capability',
                 'segmentation_type', 'vni_start', 'vni_end',
                 'gre_id_start', 'gre_id_end', 'svlan_start', 'svlan_end')

CREATE_PARAMS = ('alias', 'mtu', 'vlan_id', 'ip', 'id', 'name', 'cluster_id',
                 'ip_ranges', 'vlan_start',
                 'vlan_end', 'gateway', 'cidr', 'description', 'type',
                 'ml2_type', 'network_type', 'physnet_name', 'capability',
                 'segmentation_type', 'vni_start', 'vni_end', 'gre_id_start',
                 'gre_id_end', 'svlan_start', 'svlan_end')

DEFAULT_PAGE_SIZE = 20

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('name', 'id', 'cluster_id', 'created_at', 'updated_at')

OS_REQ_ID_HDR = 'x-openstack-request-id'


class Network(base.Resource):

    def __repr__(self):
        return "<Network %s>" % self._info

    def update(self, **fields):
        self.manager.update(self, **fields)

    def delete(self, **kwargs):
        return self.manager.delete(self)

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class NetworkManager(base.ManagerWithFind):
    resource_class = Network

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def _network_meta_from_headers(self, headers):
        meta = {'properties': {}}
        safe_decode = encodeutils.safe_decode
        for key, value in six.iteritems(headers):
            value = safe_decode(value, incoming='utf-8')
            if key.startswith('x-image-meta-property-'):
                _key = safe_decode(key[22:], incoming='utf-8')
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = safe_decode(key[13:], incoming='utf-8')
                meta[_key] = value

        for key in ['is_public', 'protected', 'deleted']:
            if key in meta:
                meta[key] = strutils.bool_from_string(meta[key])

        return self._format_network_meta_for_user(meta)

    def _network_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)

        # NOTE(flaper87): Convert to str, headers
        # that are not instance of basestring. All
        # headers will be encoded later, before the
        # request is sent.

        for key, value in six.iteritems(fields_copy):
            headers['%s' % key] = utils.to_str(value)
        return headers

    @staticmethod
    def _format_image_meta_for_user(meta):
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key]) if meta[key] else 0
                except ValueError:
                    pass
        return meta

    @staticmethod
    def _format_network_meta_for_user(meta):
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key]) if meta[key] else 0
                except ValueError:
                    pass
        return meta

    def get(self, network, **kwargs):
        """Get the metadata for a specific network.

        :param network: host object or id to look up
        :rtype: :class:`Network`
        """
        network_id = base.getid(network)
        resp, body = self.client.get('/v1/networks/%s'
                                     % urlparse.quote(str(network_id)))
        # meta = self._network_meta_from_headers(resp.headers)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))
        return Network(self, self._format_network_meta_for_user(
            body['network']))

    def data(self, image, do_checksum=True, **kwargs):
        """Get the raw data for a specific image.

        :param image: image object or id to look up
        :param do_checksum: Enable/disable checksum validation
        :rtype: iterable containing image data
        """
        image_id = base.getid(image)
        resp, body = self.client.get('/v1/images/%s'
                                     % urlparse.quote(str(image_id)))
        content_length = int(resp.headers.get('content-length', 0))
        checksum = resp.headers.get('x-image-meta-checksum', None)
        if do_checksum and checksum is not None:
            body = utils.integrity_iter(body, checksum)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return utils.IterableWithLength(body, content_length)

    def _build_params(self, parameters):
        params = {'limit': parameters.get('page_size', DEFAULT_PAGE_SIZE)}

        if 'marker' in parameters:
            params['marker'] = parameters['marker']

        sort_key = parameters.get('sort_key')
        if sort_key is not None:
            if sort_key in SORT_KEY_VALUES:
                params['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(SORT_KEY_VALUES))

        sort_dir = parameters.get('sort_dir')
        if sort_dir is not None:
            if sort_dir in SORT_DIR_VALUES:
                params['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(SORT_DIR_VALUES))

        filters = parameters.get('filters', {})
        params.update(filters)

        return params

    def list(self, **kwargs):
        """Get a list of networks.

        :param page_size: number of items to request in each paginated request
        :param limit: maximum number of networks to return
        :param marker: begin returning networks that
                       appear later in the network
                       list than that represented by this network id
        :param filters: dict of direct comparison filters that mimics the
                        structure of an network object
        :param return_request_id: If an empty list is provided, populate this
                              list with the request ID value from the header
                              x-openstack-request-id
        :rtype: list of :class:`Network`
        """
        absolute_limit = kwargs.get('limit')
        page_size = kwargs.get('page_size', DEFAULT_PAGE_SIZE)

        def paginate(qp, return_request_id=None):
            for param, value in six.iteritems(qp):
                if isinstance(value, six.string_types):
                    # Note(flaper87) Url encoding should
                    # be moved inside http utils, at least
                    # shouldn't be here.
                    #
                    # Making sure all params are str before
                    # trying to encode them
                    qp[param] = encodeutils.safe_decode(value)
            url = '/v1/clusters/%s/networks?%s' % (
                  qp['cluster_id'], urlparse.urlencode(qp)) \
                if qp.get('cluster_id', None) else\
                '/v1/networks?%s' % urlparse.urlencode(qp)
            networks, resp = self._list(url, "networks")

            if return_request_id is not None:
                return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

            for network in networks:
                yield network

        return_request_id = kwargs.get('return_req_id', None)

        params = self._build_params(kwargs)

        seen = 0
        while True:
            seen_last_page = 0
            filtered = 0
            for network in paginate(params, return_request_id):
                last_network = network.id

                if (absolute_limit is not None and
                        seen + seen_last_page >= absolute_limit):
                    # Note(kragniz): we've seen enough images
                    return
                else:
                    seen_last_page += 1
                    yield network

            seen += seen_last_page

            if seen_last_page + filtered == 0:
                # Note(kragniz): we didn't get any networks in the last page
                return

            if absolute_limit is not None and seen >= absolute_limit:
                # Note(kragniz): reached the limit of networks to return
                return

            if page_size and seen_last_page + filtered < page_size:
                # Note(kragniz): we've reached the last page of the networks
                return

            # Note(kragniz): there are more networks to come
            params['marker'] = last_network
            seen_last_page = 0

    def add(self, **kwargs):
        """Add a network

        TODO(bcwaldon): document accepted params
        """

        fields = {}
        for field in kwargs:
            if field in CREATE_PARAMS:
                fields[field] = kwargs[field]
            elif field == 'return_req_id':
                continue
            else:
                msg = 'create() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        resp, body = self.client.post('/v1/networks',
                                      headers=None,
                                      data=fields)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return Network(self, self._format_network_meta_for_user(
            body['network']))

    def delete(self, network, **kwargs):
        """Delete an network."""
        url = "/v1/networks/%s" % base.getid(network)
        resp, body = self.client.delete(url)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

    def update(self, network, **kwargs):
        """Update an network

        TODO(bcwaldon): document accepted params
        """
        fields = {}
        for field in kwargs:
            if field in UPDATE_PARAMS:
                fields[field] = kwargs[field]

        url = '/v1/networks/%s' % base.getid(network)
        resp, body = self.client.put(url, headers=None, data=fields)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return Network(self, self._format_network_meta_for_user(body[
            'network_meta']))
