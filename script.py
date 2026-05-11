#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import logging

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

@dataclass
class VMConfig:
    """VM config"""
    base_image: str
    ram_mb: int = 512
    cpu_cores: int = 1

# Path vars
DIPLOMA_IMG_FOLDER = Path("/mnt/Data_500GB/VMs/QEMU_KVM/Diploma-09.02.06")
OPENWRT_IMG_FOLDER = Path("/mnt/Data_500GB/VMs/ISOs/Network_vms/OpenWRT")

VM_CONFIG: Dict[str, VMConfig] = {
     "openwrt-Master-AP": VMConfig(
        base_image="openwrt-25.12.3-x86-64-generic-ext4-combined.img"
    ),
    #  "openwrt-AP1": VMConfig(
    #     base_image="openwrt-25.12.3-x86-64-generic-ext4-combined.img"
    # ),
    #  "openwrt-AP2": VMConfig(
    #     base_image="openwrt-25.12.3-x86-64-generic-ext4-combined.img"
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

    source_img = OPENWRT_IMG_FOLDER / VM_CONFIG[vm_name].base_image
    dest_img = DIPLOMA_IMG_FOLDER / f"{vm_name}.qcow2"

    if dry_run:
        logger.info(f"[DRY RUN] convert: {source_img} -> {dest_img}")
        return True
    
    cmd = [
        'qemu-img', 'convert', '-f', 'raw', '-O', 'qcow2',
        str(source_img), str(dest_img)
    ]
    subprocess.run(
            cmd,
            capture_output=True,
            text=True,
    )

def start_owrt_by_virt(vm_name: str):
    ram = VM_CONFIG["ram_mb"]
    vcups = VM_CONFIG["vcups"]
    disk_path = VM_CONFIG["disk_path"]
    networks = VM_CONFIG["networks"]
    vnc_port = VM_CONFIG["vnc_port"]

    cmd = [
        'sudo virt-install',
            f'--name {vm_name}',
            f'--ram {ram}',
            f'--vcpus {vcups}',
            f'--disk {disk_path},format=qcow2',
            f'--import',
            # f'--network network=default,model=virtio',
            f'{networks}',
            f'--graphics vnc,port="{vnc_port}"',
            f'--console pty,target_type=serial',
            f'--os-variant=linux20',
    ]
    subprocess.run(cmd)


def main():
    """ Main func """
    logger.info("Starting VM image creataion process")

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

if __main__ == "__main__":
    main()
