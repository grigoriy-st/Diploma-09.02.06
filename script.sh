#!/bin/bash

source vars.sh

DIPLOMA_IMG_FOLDER="/mnt/Data_500GB/VMs/QEMU_KVM/Diploma-09.02.06"
OPENWRT_IMG_FOLDER="/mnt/Data_500GB/VMs/ISOs/Network_vms/OpenWRT"

main() {
  for vm_name in "${!VMS_CONFIG[@]}"; do
    declare -n vm_config
  
    echo $vm_name
  done
}
# $1 - vm name
create_owrt_img() {
  local vm_name=$1
  qemu-img convert -f raw -O qcow2 \
    "$OPENWRT_IMG_FOLDER/openwrt-25.12.3-x86-64-generic-ext4-combined.img" \
    "$DIPLOMA_IMG_FOLDER/$vm_name.qcow2"

  if [[ $? -eq 0 ]]; then
    echo "qcow2 image of vm $vm_name is created!"
  fi
}

create_owrt_vm() {
  sudo virt-install \
    --name openwrt-ap1 \
    --ram 512 \
    --vcpus 1 \
    --disk path=$DIPLOMA_IMG_FOLDER/openwrt-vm.qcow2,format=qcow2 \
    --import \
    --network network=default,model=virtio \
    --graphics vnc,port="5920" \
    --console pty,target_type=serial \
    --os-variant=linux2022

}

main