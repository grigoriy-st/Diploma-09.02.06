#!/usr/bin/env python3

import sh
import os
import sys
import subprocess
import shutil
import logging

from pprint import pprint
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vm_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Path vars
DIPLOMA_IMG_FOLDER = Path("/mnt/Data_500GB/VMs/QEMU_KVM/Diploma-09.02.06")
OPENWRT_IMG_FOLDER = Path("/mnt/Data_500GB/VMs/ISOs/Network_vms/OpenWRT")
NETWORKS_LIST = ['default', 'br-wan', 'br-lan']
NETWORKS_FOLDER = Path("networks")

BASE_IMAGE="openwrt-25.12.3-x86-64-generic-ext4-combined.img"

class VMConfig:
    """VM config"""
    def __init__(self, disk_path, ram_mb=512, rom_gb=1, vcups=1, vnc_port=5901, net_list=[]):
        self.disk_path =disk_path
        self.ram_mb = ram_mb
        self.rom_gb = rom_gb
        self.vcups = vcups
        self.net_list = net_list
        self.vnc_port = vnc_port


VM_CONFIG: Dict[str, VMConfig] = {
     "openwrt-Master-AP": VMConfig(
        disk_path=BASE_IMAGE,
        net_list=['br-wan', 'br-lan'],
        rom_gb=1,
        vnc_port=5901
    ),
    #  "openwrt-AP1": VMConfig(
        # base_image=BASE_IMAGE,
        # net_list=['br-lan']
    # ),
    #  "openwrt-AP2": VMConfig(
        # base_image=BASE_IMAGE,
        # net_list=['br-lan']
    # ),
    # "openwrt-firewall": VMConfig(
    #     base_image="openwrt-25.12.3-x86-64-generic-ext4-combined.img"
    # ),
}

def create_openwrt_image(vm_name: str, dry_run: bool = False) -> bool:
    """
    Args:
        dry_run: If True, then show what will be done
    """

    source_img = OPENWRT_IMG_FOLDER / VM_CONFIG[f'{vm_name}'].disk_path
    dest_img = DIPLOMA_IMG_FOLDER / f"{vm_name}.qcow2"
    print(
        f'sourec img: {source_img}',
        f'dest_img: {dest_img}'
    )
    rom = VM_CONFIG[f'{vm_name}'].rom_gb

    if dry_run:
        logger.info(f"[DRY RUN] convert: {source_img} -> {dest_img}")
        return True
    
    cmd = [
        'qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2',
        '-o', f'size={rom}',
        str(source_img), str(dest_img)
    ]
    subprocess.run(
            cmd,
            capture_output=True,
            text=True,
    )

def start_owrt_by_virt(vm_name: str):
    ram = VM_CONFIG[f'{vm_name}'].ram_mb
    vcups = VM_CONFIG[f'{vm_name}'].vcups
    disk_path = VM_CONFIG[f'{vm_name}'].disk_path
    net_list = VM_CONFIG[f'{vm_name}'].net_list
    # network_args = prepare_net_args(net_list) # list of net args to virt-install command
    vnc_port = VM_CONFIG[f'{vm_name}'].vnc_port

    cmd = [
    'sudo', 'virt-install',
        '--name', f'{vm_name}',
        '--ram', f'{ram}',
        '--vcpus', f'{vcups}',
        '--disk', f'path={DIPLOMA_IMG_FOLDER}/{vm_name}.qcow2,format=qcow2',
        '--import',
        '--graphics', f'vnc,port="{vnc_port}"',
        '--console', 'pty,target_type=serial',
        '--os-variant=linux2022',
        '--noautoconsole',
        '--wait', '-1'
    ]

    cmd.extend(['--network=default'])
    for net in net_list:
        cmd.extend(['--network', f'bridge={net},model=virtio'])

    pprint(cmd)

    result = subprocess.run(cmd)
    # cmd = [
    #     'sudo virt-install',
    #         f'--name {vm_name}',
    #         f'--ram {ram}',
    #         f'--vcpus {vcups}',
    #         f'--disk {disk_path},format=qcow2',
    #         f'--import',
    #         f'{network_args}',
    #         f'--graphics vnc,port="{vnc_port}"',
    #         f'--console pty,target_type=serial',
    #         f'--os-variant=linux20',
    # ]
    # subprocess.run(cmd)

def prepare_net_args(networks: list) -> list:
    result_net_args = []
    for net_name in networks:
        arg_line = f'--network bridge={net_name},model=virtio '
        result_net_args.append(arg_line)
    
    return result_net_args

def create_network(networks: list) -> bool:
    net_exists = sh.sudo.virsh("net-list --name").splitlines()[2:]
    print(net_exists)
    exit

    for net_name in networks:
        if net_name in net_exists:
            continue

        xml_path = os.path.join(NETWORKS_FOLDER, f'{net_name}.xml')
        if not os.path.exists(xml_path):
            print(f"Error: file {xml_path} not found")
            return False

        net_def_res = subprocess.run(
            ['sudo', 'virsh', 'net-define', f'{NETWORKS_FOLDER}/{net_name}.xml'],
            capture_output=True,
            text=True
        )

        if net_def_res != 0:
            print(f"Error in net define: {net_def_res}")

        net_auto_res = subprocess.run(
            ['sudo', 'virsh', 'net-autostart', f'{net_name}'],
            capture_output=True,
            text=True
        )
        
        if net_auto_res != 0:
            print(f"Error in net autostart: {net_auto_res}")

        net_start_res = subprocess.run(
            ['sudo', 'virsh', 'net-start', f'{net_name}'],
            capture_output=True,
            text=True
        )
        if net_start_res != 0:
            print(f"Error in net start: {net_start_res}")

def main():
    """ Main func """
    logger.info("Starting VM image creataion process")

    # create_openwrt_image('openwrt-Master-AP')
    # create_network(NETWORKS_LIST)
    start_owrt_by_virt('openwrt-Master-AP')
    sys.exit()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--vm')
    args = parser.parse_args()

    vms_to_process = [args.vm] if args.vm else VM_CONFIG.keys()

    success_count = 0
    failed_vms = []

    for vm_name in vms_to_process:
        if vm_name not in VM_CONFIG:
            logger.warning(f"Unknown VM: {vm_name}")
        
        logger.info(f"Processing {vm_name}...")
    
    if create_openwrt_image(vm_name,dry_run=args.dry_run):
        success_count += 1
    else:
        failed_vms.append(vm_name)

    logger.info(f"=== Summary ===")
    logger.info(f"Success: {success_count}, Failed: {len(failed_vms)}")
    if failed_vms:
        logger.warning(f"Failed VMs: {', '.join(failed_vms)}")
        sys.exit(1)
    else:
        logger.info("All VMs processed successfully!")

if __name__ == "__main__":
    main()
