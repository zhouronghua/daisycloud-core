# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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


from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.environment.cluster import views
from openstack_dashboard.dashboards.environment.cluster import net_plane
from openstack_dashboard.dashboards.environment.cluster import role
from openstack_dashboard.dashboards.environment.cluster import create_cluster
from openstack_dashboard.dashboards.environment.cluster import modify_cluster

CLUSTER = r'^(?P<cluster_id>[^/]+)/%s$'
CLUSTER_HOST = r'^(?P<cluster_id>[^/]+)/(?P<host_id>[^/]+)/%s$'

urlpatterns = patterns(
    'openstack_dashboard.dashboards.environment.cluster.views',
    url(r'^$', views.ClusterView.as_view(), name='index'),
    url(r'^create$', create_cluster.CreateView.as_view(), name="create"),
    url(r'^create_submit$', create_cluster.create_submit,
        name="create_submit"),
    url(CLUSTER % 'modify', modify_cluster.ModifyView.as_view(),
        name='modify'),
    url(CLUSTER % 'overview', views.ClusterView.as_view(), name='overview'),
    url(CLUSTER % 'upgrade', views.upgrade_cluster, name='upgrade'),
    url(CLUSTER % 'update_deploy_info',
        views.update_deploy_info,
        name='update_deploy_info'),
    url(CLUSTER % 'uninstall', views.uninstall_version, name='uninstall'),
    url(r'get_cluster/$', modify_cluster.GetCluster, name='get_cluster'),
    url(r'get_clusters/$', modify_cluster.GetClusters, name='get_clusters'),
    url(CLUSTER % 'modify_submit/$', modify_cluster.modify_submit,
        name='modify_submit'),
    url(CLUSTER % 'set_cluster_auto_scale/$',
        modify_cluster.set_cluster_auto_scale,
        name='set_cluster_auto_scale'),
    url(r'get_ha_role_info/$', role.get_ha_role_info,
        name='get_ha_role_info'),
    url(r'get_computer_role_info/$', role.get_computer_role_info,
        name='get_computer_role_info'),
    url(r'get_role_info/$', role.get_role_info,
        name='get_role_info'),
    url(CLUSTER % 'add_net_plane/',
        net_plane.add_net_plane,
        name='add_net_plane'),
    url(CLUSTER % 'delete_net_plane',
        net_plane.delete_net_plane,
        name='delete_net_plane'),
)