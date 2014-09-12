#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import optparse
import sys
import time

import boto.ec2
import boto.ec2.blockdevicemapping
import boto.exception


DEFAULT = {
    'region_name': 'us-east-1',
    'aws_access_key_id': None,
    'aws_secret_access_key': None,
    'base_ec2_name': None,
    'base_ec2_id': None,
    'hostname': None,
    'override_ami_id': None,
    'override_security_group_ids': None,
    'override_subnet_id': None,
    'override_instance_type': None,
    'override_private_ip_address': None,
    'override_terminate_protection': None,
    'override_shutdown_behavior': None,
    'override_root_ebs_size': None,
    'override_root_ebs_type': None,
    'override_root_ebs_iops': None,
    'override_optional_ebs_size': None,
    'override_optional_ebs_device': None,
    'override_optional_ebs_type': None,
    'override_optional_ebs_iops': None,
    'userdata': None,
    'dry_run': False,
    'log_level': 'INFO',
    'wait_until_running': False
}


def get_args():

    usage = (
        'Create EC2 instance like "AWS Launch more like this".'
    )
    parser = optparse.OptionParser(usage=usage)

    aws_credential_option_group = optparse.OptionGroup(
        parser,
        'AWS credential parameters'
    )

    aws_credential_option_group.add_option(
        '--region-name', '-r',
        type='string', default=DEFAULT['region_name'],
        dest='region_name',
        help='AWS Region Name.'
    )
    aws_credential_option_group.add_option(
        '--aws-access-key-id', '-i',
        type='string', default=DEFAULT['aws_access_key_id'],
        dest='aws_access_key_id',
        help='AWS Access Key Id'
    )
    aws_credential_option_group.add_option(
        '--aws-secret-access-key', '-k',
        type='string', default=DEFAULT['aws_secret_access_key'],
        dest='aws_secret_access_key',
        help='AWS Secret Access Key'
    )
    parser.add_option_group(aws_credential_option_group)

    override_ec2_option_group = optparse.OptionGroup(
        parser,
        'Override Instance Options'
    )

    override_ec2_option_group.add_option(
        '--override-ami-id', '-a',
        type='string', default=DEFAULT['override_ami_id'],
        dest='override_ami_id',
        help='When you want to override new instance AMI, use this option.'
    )
    override_ec2_option_group.add_option(
        '--override-security-group-ids', '-s',
        type='string', default=DEFAULT['override_security_group_ids'],
        dest='override_security_group_ids',
        help=(
            'When you want to override new instance security groups, '
            'use this option. '
            'Use comma as delimiter.'
        )
    )
    override_ec2_option_group.add_option(
        '--override-subnet-id', '-c',
        type='string', default=DEFAULT['override_subnet_id'],
        dest='override_subnet_id',
        help='when you want to override new instance subnet, use this option.'
    )
    override_ec2_option_group.add_option(
        '--override-instance-type', '-t',
        type='string', default=DEFAULT['override_instance_type'],
        dest='override_instance_type',
        help=(
            'when you want to override new instance instance type, '
            'use this option.'
        )
    )
    override_ec2_option_group.add_option(
        '--override-private-ip-address', '-x',
        type='string', default=DEFAULT['override_private_ip_address'],
        dest='override_private_ip_address',
        help=(
            'when you want to override new instance private IP address, '
            'use this option.'
        )
    )
    override_ec2_option_group.add_option(
        '--override-terminate-protection', '-d',
        type='string', default=DEFAULT['override_terminate_protection'],
        dest='override_terminate_protection',
        help=(
            'When you want to '
            'override new instance terminate protection option, '
            'use this option.'
        )
    )
    override_ec2_option_group.add_option(
        '--override-shutdown-behavior', '-b',
        type='choice', default=DEFAULT['override_shutdown_behavior'],
        choices=[
            'stop',
            'terminate'
        ],
        dest='override_shutdown_behavior',
        help=(
            'When you want to override new instance shutdown behavior, '
            'use this option.'
        )
    )
    parser.add_option_group(override_ec2_option_group)

    override_ebs_option_group = optparse.OptionGroup(
        parser,
        'Override EBS Options'
    )
    override_ebs_option_group.add_option(
        '--override-root-ebs-size', '-v',
        type='int', default=DEFAULT['override_root_ebs_size'],
        dest='override_root_ebs_size',
        help=(
            'When you want to override root EBS volume size, '
            'use this option. Unit of this option is GB.'
        )
    )
    override_ebs_option_group.add_option(
        '--override-root-ebs-type', '-f',
        type='choice', default=DEFAULT['override_root_ebs_type'],
        choices=[
            'standard',
            'consistent-iops'
        ],
        dest='override_root_ebs_type',
        help=(
            'When you want to override root EBS volume type, '
            'use this option.'
        )
    )
    override_ebs_option_group.add_option(
        '--override-root-ebs-iops', '-o',
        type='int', default=DEFAULT['override_root_ebs_iops'],
        dest='override_root_ebs_iops',
        help=(
            'When you want to override root EBS iops, '
            'use this option.'
        )
    )
    override_ebs_option_group.add_option(
        '--override-optional-ebs-size', '-V',
        type='int', default=DEFAULT['override_optional_ebs_size'],
        dest='override_optional_ebs_size',
        help=(
            'When you want to override optional EBS size, '
            'use this option. Unit of this option is GB.'
        )
    )
    override_ebs_option_group.add_option(
        '--override-optional-ebs-device', '-G',
        type='string', default=DEFAULT['override_optional_ebs_device'],
        dest='override_optional_ebs_device',
        help=(
            'When you want to override optional EBS attached device, '
            'use this option. e.x: /dev/sdb'
        )
    )
    override_ebs_option_group.add_option(
        '--override-optional-ebs-type', '-F',
        type='choice', default=DEFAULT['override_optional_ebs_type'],
        choices=[
            'standard',
            'consistent-iops'
        ],
        dest='override_optional_ebs_type',
        help=(
            'When you want to override optional EBS volume type, '
            'use this option.'
        )
    )
    override_ebs_option_group.add_option(
        '--override-optional-ebs-iops', '-O',
        type='int', default=DEFAULT['override_optional_ebs_iops'],
        dest='override_optional_ebs_iops',
        help=(
            'When you want to override optional EBS iops, '
            'use this option.'
        )
    )
    parser.add_option_group(override_ebs_option_group)

    parser.add_option(
        '--base-ec2-name', '-N',
        type='string', default=DEFAULT['base_ec2_name'],
        dest='base_ec2_name',
        help='Based EC2 instance "Name" tag.'
    )
    parser.add_option(
        '--base-ec2-id', '-I',
        type='string', default=DEFAULT['base_ec2_id'],
        dest='base_ec2_id',
        help='Based EC2 instance id.'
    )
    parser.add_option(
        '--hostname', '-H',
        type='string', default=DEFAULT['hostname'],
        help='New EC2 instance hostname(Name Tag).'
    )
    parser.add_option(
        '--userdata', '-U',
        type='string', default=DEFAULT['userdata'],
        help='Injected AWS "Userdata".'
    )
    parser.add_option(
        '--dry-run', '-D',
        type='string', default=DEFAULT['dry_run'],
        dest='dry_run',
        help='Dry run flag. Please specify "true" or "false".'
    )
    parser.add_option(
        '--wait-until-running', '-W',
        action='store_true', default=DEFAULT['wait_until_running'],
        dest='wait_until_running',
        help='Wait until new instance status is running.'
    )
    parser.add_option(
        '--log-level', '-L',
        type='choice', default=DEFAULT['log_level'],
        choices=[
            'DEBUG',
            'INFO',
            'WARNING',
            'ERROR',
            'CRITICAL'
        ],
        help=(
            'Injected AWS "Userdata".'
        )
    )

    return parser.parse_args()[0]


class EC2MoreLikeThisException(BaseException):

    def __init__(self, message):
        super(EC2MoreLikeThisException, self).__init__(message)


def set_log_level(log_level='DEBUG'):
    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        level=getattr(logging, log_level)
    )


def validate_options(options):

    if not options.aws_access_key_id:
        raise EC2MoreLikeThisException(
            '"--aws-access-key-id" option is required.'
        )

    if not options.aws_secret_access_key:
        raise EC2MoreLikeThisException(
            '"--aws-secret-access-key" option is required.'
        )

    if (
        not options.base_ec2_name and
        not options.base_ec2_id
    ):
        raise EC2MoreLikeThisException(
            '"--base-ec2-name" or "--base-ec2-id"'
            'specify any.'
        )


def convert_options(options):

    if options.override_terminate_protection:
        if options.override_terminate_protection.lower() == 'true':
            options.override_terminate_protection = True
        elif options.override_terminate_protection.lower() == 'false':
            options.override_terminate_protection = False
        else:
            raise EC2MoreLikeThisException(
                (
                    '"--override-terminate-protection" option must be '
                    '"true" or "false"'
                )
            )

    if options.dry_run:
        if options.dry_run.lower() == 'true':
            options.dry_run = True
        elif options.dry_run.lower() == 'false':
            options.dry_run = False
        else:
            raise EC2MoreLikeThisException(
                (
                    '"--dry-run" option must be "true" or "false"'
                )
            )

    if options.override_security_group_ids:
        try:
            options.override_security_group_ids = [
                entry.strip() for entry in (
                    options.override_security_group_ids.split(',')
                )
            ]
        except:
            raise EC2MoreLikeThisException(
                (
                    '--override-security-group-ids option '
                    'must be separated by comma.'
                )
            )

    return options


def create_conn(region_name, aws_access_key_id, aws_secret_access_key):

    try:
        conn = boto.ec2.connect_to_region(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    except Exception as exception:
        raise EC2MoreLikeThisException(
            exception.__str__()
        )

    if conn is None:
        raise EC2MoreLikeThisException(
            'Maybe failed to AWS authentication.'
        )

    return conn


def verify_ec2_instance_by_name(conn, name):
    reservations = conn.get_all_instances(
        filters={'tag:Name': name}
    )
    if len(reservations) > 0:
        raise EC2MoreLikeThisException(
            'Specified instance name {0} is already used.'.format(name)
        )
    return True


def verify_ec2_instance_by_private_ip_address(conn, private_ip_address):
    all_nics = conn.get_all_network_interfaces()
    all_private_ips = [
        entry.private_ip_address for entry in all_nics
    ]
    logging.debug(
        'All private IP addresses are {0}'.format(all_private_ips)
    )
    if private_ip_address in all_private_ips:
        raise EC2MoreLikeThisException(
            'Specified private IP {0} is already used.'
            ''.format(private_ip_address)
        )
    return True


def get_base_ec2_instance(conn,
                          base_ec2_name=None,
                          base_ec2_id=None):
    """
    Get EC2 instance by Name tag or instance id.
    :param conn: EC2 connection
    :type conn: boto.ec2.EC2Connection
    :param base_ec2_name: Name tag of based ec2 instance
    :type base_ec2_name: str
    :param base_ec2_id: Instance id of based ec2 instance
    :type base_ec2_id: str
    :rtype: list
    :return: EC2 Reservation
    """

    if not base_ec2_name and not base_ec2_id:
        raise EC2MoreLikeThisException(
            '"base_ec2_name" or "base_ec2_id" argument is required.'
        )
    elif base_ec2_name and base_ec2_id:
        raise EC2MoreLikeThisException(
            '"base_ec2_name" and "base_ec2_id" arguments are exclusive.'
        )
    elif base_ec2_name:
        logging.debug(
            'Use "Name" tag to searching based EC2 instance.'
        )
        try:
            reservations = conn.get_all_instances(
                filters={
                    'tag:Name': base_ec2_name
                }
            )
            instances = reservations[0].instances
            if len(instances) > 1:
                raise EC2MoreLikeThisException(
                    'Found more then two instances...'
                )
            elif len(instances) <= 0:
                raise EC2MoreLikeThisException(
                    'Instance which has "{0}" as "Name" tag does not exist...'
                    ''.format(base_ec2_name)
                )
            logging.debug(
                'Base instance is {0}.'.format(instances)
            )
            return instances[0]
        except boto.exception.EC2ResponseError as exception:
            raise EC2MoreLikeThisException(
                exception.__str__()
            )
    elif base_ec2_id:
        logging.debug(
            'Use "InstanceId" tag to searching based EC2 instance.'
        )
        try:
            reservations = conn.get_all_instances(instance_ids=[base_ec2_id])
            instances = reservations[0].instances
            if len(instances) <= 0:
                raise EC2MoreLikeThisException(
                    'Instance ID: {0} does not exist...'.format(base_ec2_id)
                )
            logging.debug(
                'Base instance is {0}.'.format(instances)
            )
            return instances[0]
        except boto.exception.EC2ResponseError as exception:
            raise EC2MoreLikeThisException(
                exception.__str__()
            )


def get_ami(conn, ami_id):

    try:
        result = conn.get_all_images(image_ids=[ami_id])
        logging.debug(
            'Based "ami" is {0}'.format(result)
        )
        return result[0]
    except boto.exception.EC2ResponseError as exception:
        raise EC2MoreLikeThisException(
            exception.__str__()
        )


class MoreLikeThisEC2Instance(object):

    def __init__(self, conn=None):
        self.conn = conn
        self.base_ec2_instance = None
        self.base_block_device_mapping = None
        self.ec2_attributes = dict()
        self.ec2_tags = dict()
        self.device_mapping = dict()
        self.base_image = None

    def set_ec2_connection(self, conn):
        self.conn = conn

    def set_base_ec2_instance(self, ec2_instance):
        self.base_ec2_instance = ec2_instance

        self.ec2_attributes['key_name'] = self.base_ec2_instance.key_name
        self.ec2_attributes['security_group_ids'] = (
            [
                entry.id for entry in self.base_ec2_instance.groups
            ]
        )
        self.ec2_attributes['subnet_id'] = self.base_ec2_instance.subnet_id
        self.ec2_attributes['instance_type'] = (
            self.base_ec2_instance.instance_type
        )
        self.ec2_attributes['private_ip_address'] = None
        try:
            self.ec2_attributes['disable_api_termination'] = (
                self.base_ec2_instance.get_attribute(
                    'disableApiTermination'
                ).get('disableApiTermination', False)
            )
        except AttributeError:
            self.ec2_attributes['disable_api_termination'] = None
            logging.warn(
                'Instance doesn\'t have "disableApiTermination" attribute.'
            )
        try:
            self.ec2_attributes['instance_initiated_shutdown_behavior'] = (
                self.base_ec2_instance.get_attribute(
                    'instanceInitiatedShutdownBehavior'
                ).get('instanceInitiatedShutdownBehavior', 'stop')
            )
        except AttributeError:
            self.ec2_attributes['instance_initiated_shutdown_behavior'] = None
            logging.warn(
                'Instance doesn\'t have '
                '"instanceInitiatedShutdownBehavior" attribute.'
            )
        self.ec2_tags = self.base_ec2_instance.tags

    def set_base_block_device_mapping(self, block_device_mapping):
        if len(block_device_mapping.keys()) > 2:
            raise NotImplementedError(
                (
                    'Sorry!! We haven\'t implement "Launch more like this" '
                    'to ec2 instance that has EBSs more than two.'
                )
            )

        self.base_block_device_mapping = block_device_mapping

        for key, value in self.base_block_device_mapping.items():
            volume = self.conn.get_all_volumes(
                volume_ids=value.volume_id
            )[0]
            self.device_mapping[key] = dict(
                size=volume.size,
                volume_type=volume.type,
                iops=volume.iops,
                encrypted=volume.encrypted
            )

    def set_base_image(self, base_image):
        self.base_image = base_image

    def apply_ec2_option(self, name, value):
        if value and name in self.ec2_attributes.keys():
            self.ec2_attributes[name] = value
        else:
            raise EC2MoreLikeThisException(
                'EC2 instance has no attributes {0}'.format(name)
            )

    def apply_ec2_hostname(self, hostname):
        self.ec2_tags['Name'] = hostname

    def apply_root_ebs_option(self, name, value, device='/dev/sda1'):
        """
        Apply ebs option to root device.
        If specified device does not exist, you cannot set parameter.
        :param name: parameter name e.x: size, type or iops
        :type name: str
        :param value: parameter value
        :param device: device name. e.x: /dev/sda1
        :type device: str
        """
        if device in self.device_mapping.keys():
            self.device_mapping[device][name] = value
        else:
            raise EC2MoreLikeThisException(
                'Seems to no device {0}, cannot override parameters.'
                ''.format(device)
            )

    def apply_optional_ebs_option(self, name, value, device=None):
        """
        Apply ebs option to optional device.
        :param name: parameter name e.x: size, type or iops
        :type name: str
        :param value: parameter value
        :param device: device name. e.x: /dev/sdh
        :type device: str
        """
        devices = self.device_mapping.keys()
        devices.remove('/dev/sda1')
        current_optional_device = devices[0]
        if not device:
            device = devices[0]
        if device in self.device_mapping.keys():
            self.device_mapping[device][name] = value
        else:
            logging.info(
                'Change device name. In {0} out {1}'
                ''.format(device, current_optional_device)
            )
            self.device_mapping[device] = (
                self.device_mapping.pop(current_optional_device)
            )
            self.device_mapping[device][name] = value

    def _construct_device_mapping(self, raw_options):
        block_device_mapping = boto.ec2.blockdevicemapping.BlockDeviceMapping(
            connection=self.conn
        )
        for key, value in raw_options.items():
            block_device_mapping[key] = (
                boto.ec2.blockdevicemapping.BlockDeviceType(
                    connection=self.conn,
                    size=value['size'],
                    volume_type=value['volume_type'],
                    iops=value['iops']
                )
            )
        return block_device_mapping

    def add_name_tag_to_volume(self, instance_id, block_device_mapping):
        """
        Set Instance ID to tag of volume's Name.
        :param instance_id: Instance ID (Any string)
        :type instance_id: str
        :param block_device_mapping: Block device mapping of instance.
        :type block_device_mapping:
        boto.ec2.blockdevicemapping.BlockDeviceMapping
        :return: True
        :rtype: bool
        """

        for key, value in block_device_mapping.items():
            tag_value = (
                '{instance_id}:{device}'
                ''.format(
                    instance_id=instance_id,
                    device=key
                )
            )
            try:
                volume = self.conn.get_all_volumes(
                    volume_ids=[value.volume_id]
                )[0]
                volume.add_tag(
                    key='Name',
                    value=tag_value
                )
                logging.info(
                    'Add tag {{Name: {value}}} to {device}'
                    ''.format(
                        value=tag_value,
                        device=key
                    )
                )
            except Exception as exception:
                raise EC2MoreLikeThisException(
                    exception.__str__()
                )

        return block_device_mapping

    def run(self,
            wait_until_running=True,
            checking_state_term=5,
            checking_count_threshold=60,
            dry_run=False):
        run_params = self.ec2_attributes.copy()
        run_params['dry_run'] = dry_run
        if dry_run:
            logging.info(
                (
                    'You set dry run flag is true!! '
                    'Create new EC2 instance with following options.'
                )
            )
            print('EC2 options: ')
            for key, value in run_params.items():
                print('{0}: {1}'.format(key, value))
            print('EBS options: ')
            for key, value in self.device_mapping.items():
                print('{0}: {1}'.format(key, value))
            print('Tags: ')
            for key, value in self.ec2_tags.items():
                print('{0}: {1}'.format(key, value))

        if not dry_run:
            run_params['block_device_map'] = self._construct_device_mapping(
                self.device_mapping
            )
            reservation = self.base_image.run(
                **run_params
            )
            instance = reservation.instances[0]

            if self.ec2_tags:
                for key, value in self.ec2_tags.items():
                    instance.add_tag(
                        key=key,
                        value=value
                    )
                logging.info(
                    'Set tag: {{{0}: {1}}}'.format(key, value)
                )
            else:
                logging.debug(
                    'You specify no tags for new EC2 instance.'
                )

            if instance.block_device_mapping:
                self.add_name_tag_to_volume(
                    instance_id=instance.id,
                    block_device_mapping=instance.block_device_mapping
                )

            if wait_until_running:
                pending_count = 0
                while (
                    self.conn.get_all_instance_status(
                        instance.id
                    )[0].state_name.lower() == 'pending'
                ):
                    logging.info(
                        'Created instance state is "pending"'
                    )
                    time.sleep(checking_state_term)
                    pending_count += 1

                    if pending_count > checking_count_threshold:
                        logging.warn(
                            'Checking instance state timeout.'
                        )
                        break
                return instance

            else:
                return instance


def main():
    options = get_args()
    validate_options(options)
    options = convert_options(options=options)
    set_log_level(log_level=options.log_level)

    conn = create_conn(
        region_name=options.region_name,
        aws_access_key_id=options.aws_access_key_id,
        aws_secret_access_key=options.aws_secret_access_key
    )
    if options.hostname:
        verify_ec2_instance_by_name(
            conn=conn,
            name=options.hostname
        )
    if options.override_private_ip_address:
        verify_ec2_instance_by_private_ip_address(
            conn=conn,
            private_ip_address=options.override_private_ip_address
        )
    base_ec2_instance = get_base_ec2_instance(
        conn=conn,
        base_ec2_name=options.base_ec2_name,
        base_ec2_id=options.base_ec2_id
    )
    if not options.override_ami_id:
        base_image = get_ami(
            conn=conn,
            ami_id=base_ec2_instance.image_id
        )
    else:
        base_image = get_ami(
            conn=conn,
            ami_id=options.override_ami_id
        )
    more_like_this_ec2 = MoreLikeThisEC2Instance()
    more_like_this_ec2.set_ec2_connection(conn=conn)
    more_like_this_ec2.set_base_ec2_instance(
        ec2_instance=base_ec2_instance
    )
    more_like_this_ec2.set_base_block_device_mapping(
        base_ec2_instance.block_device_mapping
    )
    more_like_this_ec2.set_base_image(
        base_image=base_image
    )
    # apply override options
    if options.hostname:
        more_like_this_ec2.apply_ec2_hostname(
            hostname=options.hostname
        )
    if options.override_security_group_ids:
        more_like_this_ec2.apply_ec2_option(
            name='security_group_ids',
            value=options.security_group_ids
        )
    if options.override_subnet_id:
        more_like_this_ec2.apply_ec2_option(
            name='subnet_id',
            value=options.override_subnet_id
        )
    if options.override_instance_type:
        more_like_this_ec2.apply_ec2_option(
            name='instance_type',
            value=options.override_instance_type
        )
    if options.override_private_ip_address:
        more_like_this_ec2.apply_ec2_option(
            name='private_ip_address',
            value=options.override_private_ip_address
        )
    if options.override_terminate_protection:
        more_like_this_ec2.apply_ec2_option(
            name='disable_api_termination',
            value=options.override_terminate_protection
        )
    if options.override_shutdown_behavior:
        more_like_this_ec2.apply_ec2_option(
            name='instance_initiated_shutdown_behavior',
            value=options.override_shutdown_behavior
        )
    if options.override_root_ebs_size:
        more_like_this_ec2.apply_root_ebs_option(
            name='size',
            value=options.override_root_ebs_size
        )
    if options.override_root_ebs_type:
        more_like_this_ec2.apply_root_ebs_option(
            name='type',
            value=options.override_root_ebs_type
        )
    if options.override_root_ebs_iops:
        more_like_this_ec2.apply_root_ebs_option(
            name='iops',
            value=options.override_root_ebs_iops
        )
    if options.override_optional_ebs_size:
        more_like_this_ec2.apply_optional_ebs_option(
            name='size',
            value=options.override_optional_ebs_size,
            device=options.override_optional_ebs_device
        )
    if options.override_optional_ebs_type:
        more_like_this_ec2.apply_optional_ebs_option(
            name='type',
            value=options.override_optional_ebs_type,
            device=options.override_optional_ebs_device
        )
    if options.override_optional_ebs_iops:
        more_like_this_ec2.apply_optional_ebs_option(
            name='iops',
            value=options.override_optional_ebs_iops,
            device=options.override_optional_ebs_device
        )

    more_like_this_ec2.run(
        wait_until_running=options.wait_until_running,
        checking_state_term=10,
        checking_count_threshold=60,
        dry_run=options.dry_run
    )


if __name__ == '__main__':
    try:
        main()
    except EC2MoreLikeThisException as exception:
        logging.error(
            exception.__str__()
        )
        sys.exit(1)
