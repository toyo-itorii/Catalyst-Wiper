# 1. Boot in Rommon
# 2. flash_init
# 3. rename flash:config.text flash:config.old
# 4. boot

# Once booted, run the following commands to remove the old vlans

# 1. erase startup-config
# 2. delete flash:vlan.dat
# 3. reload