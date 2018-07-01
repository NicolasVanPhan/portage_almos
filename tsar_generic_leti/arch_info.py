#!/usr/bin/env python

from arch_classes import *

#######################################################################################
#   file   : arch_info.py  
#   date   : june 2018
#   author : Alain Greiner
#
#  This file describes the <tsar_generic_leti> architecture for ALMOS-MKH.
#######################################################################################
#  This file defines a specific instance of the "tsar_generic_leti" architecture.
#  It is used to generate the "hard_config.h" file, 
#  used to configure the hardware architecture, and the "arch_info.bin" file, used by 
#  the ALMOS-MK bootloader.
#
#  The constructor prototype format is imposed by the genarch.py application,
#  and should not be modified. 
#  The default argument values are for the TSARLET 16 cores prototype.
#
#  The "tsar_generic_leti" architecture  includes 5 external peripherals located 
#  in cluster[x_size-1][y_size-1]: TTY, IOC, FBF, NIC, PIC.
#  The upper row (y = y_size-1) does not contain processors or memory.
#  The "tsar_generic_leti" does not use the IOB component.
#  It does not use an external ROM, as the preloader code is (pre)loaded
#  at address 0x0, in the physical memory of cluster[0][0].
#
#  Two backup peripherals one (one TXT_TTY and one IOC_BDV) are connected
#  on local interconnect in cluster 0.
#
#  The "constructor" parameters (defined in Makefile) are:
#  - x_size         : number of clusters in a row (from 1 to 16)
#  - y_size         : number of clusters in a column (from 1 to 16)
#  - nb_cores       : number of cores per cluster (from 1 to 4)
#  - nb_ttys        : number of TTY channels (from 1 to 8)
#  - nb_nics        : number of NIC channels (from 1 to 2)
#  - fbf_width      : frame_buffer width = frame_buffer heigth
#  - ioc_type       : can be 'IOC_BDV','IOC_HBA','IOC_SDC','IOC_RDK' 
#
#  The others hardware parameters are defined below :
#  - x_width        : number of bits for x coordinate
#  - y_width        : number of bits for y coordinate
#  - p_width        : number of bits for local core index
#  - paddr_width    : number of bits for physical address
#  - irq_per_proc   : number of input IRQs per processor
#  - io_cxy         : IO_cluster identifier
#  - boot_cxy       : boot_cluster identifier
#  - cache_line     : number of bytes in cache line (64 for tsar)
#  - devices_max    : max number of internal devices per cluster
#####################################################################################


########################
def arch( x_size    = 2,
          y_size    = 3,
          nb_cores  = 4,
          nb_ttys   = 3,
          nb__nics  = 1,
          fbf_width = 128,
          ioc_type  = 'IOC_BDV'):

    ### architecture constants

    p_width         = 2 
    x_width         = 4
    y_width         = 4 
    paddr_width     = 40 
    irq_per_proc    = 4                                    # NetBSD constraint
    io_cxy          = ((x_size-1)<<y_width) + (y_size-1)   # upper right cluster
    boot_cxy        = 0
    cache_line      = 64
    devices_max     = 16  
    reset_address   = 0x00000000                           # LETI constraint

    ### constructors parameters checking

    assert( nb_cores <= 4 )

    assert( x_size <= (1 << x_width) )

    assert( (y_size > 1) and (y_size <= (1 << y_width)) )

    assert( (nb_ttys >= 1) and (nb_ttys <= 8) )

    assert( (nb_nics >= 1) and (nb_nics <= 2) )

    assert( ioc_type in ['IOC_BDV','IOC_HBA','IOC_SDC','IOC_SPI','IOC_RDK'] )

    assert( ((boot_cxy >> y_width) < x_size) and ((boot_cxy & ((1<<y_width)-1)) < (y_size - 1) ) )

    ### define type and name 

    platform_name  = 'tsar_leti_%d_%d_%d' % ( x_size, y_size, nb_cores )

    ### define physical segments replicated in all non-IO clusters
    ### the base address is extended by the cxy (8 bits)

    ram_base = 0x0000000000
    ram_size = 0x4000000                  # 64 Mbytes

    xcu_base = 0x00F0000000
    xcu_size = 0x1000                     # 4 Kbytes

    mmc_base = 0x00F1000000
    mmc_size = 0x1000                     # 4 Kbytes

    ### define physical segments for external peripherals in IO cluster
    ## These segments are extended byb the IO_cluster cxy (8bits)

    ioc_base = 0x00F2000000
    ioc_size = 0x1000                     # 4kbytes

    fbf_base = 0x00F3000000
    fbf_size = fbf_width * fbf_width      # fbf_width * fbf_width bytes

    tty_base = 0x00F4000000
    tty_size = 0x8000                     # 4 Kbytes * 8 channels

    nic_base = 0x00F7000000
    nic_size = 0x4000                     # 4 Kbytes * 4 channels

    pic_base = 0x00F9000000
    pic_size = 0x1000                     # 4 Kbytes

    #############################
    ### call header constructor
    #############################

    archi = Archinfo( name           = platform_name,
                      x_size         = x_size,
                      y_size         = y_size,
                      cores_max      = nb_cores,
                      devices_max    = devices_max,
                      paddr_width    = paddr_width,
                      x_width        = x_width,
                      y_width        = y_width,
                      irqs_per_core  = irqs_per_core,
                      io_cxy         = io_cxy,          
                      boot_cxy       = boot_cxy,
                      cache_line     = cache_line,
                      reset_address  = reset_address,
                      p_width        = p_width )

    ###########################
    ### Hardware Description
    ###########################

    for x in xrange( x_size ):
        for y in xrange( y_size ):
            cluster_xy = (x << y_width) + y;
            offset     = cluster_xy << (paddr_width - x_width - y_width)
 
            ### components replicated in all clusters but the upper row
            if ( y < (y_size - 1) ):

                ram = archi.addDevice( ptype = 'RAM_SCL',
                                       base  = ram_base + offset, 
                                       size  = ram_size )

                mmc = archi.addDevice( ptype = 'MMC_TSR',
                                       base  = mmc_base + offset, 
                                       size  = mmc_size )

                xcu = archi.addDevice( ptype    = 'ICU_XCU',
                                       base     = xcu_base + offset, 
                                       size     = xcu_size, 
                                       channels = nb_cores * irq_per_proc, 
                                       arg0 = 16, arg1 = 16, arg2 = 16 )

                archi.addIrq( dstdev = xcu,
                              port   = 8, 
                              srcdev = mmc )

                ### TTY and IOC backup
                if ( x==0 ) and ( y==0 ):
                    tty_bak = archi.addDevice( ptype    = 'TXT_TTY',
                                               base     = tty_base + offset,
                                               size     = tty_size, 
                                               channels = nb_ttys )

                    archi.addIrq( dstdev  = xcu, 
                                  port    = TODO 
                                  srcdev  = tty_bak,
                                  channel = 0,
                                  is_rx   = False )

                    ioc_bak = archi.addDevice( ptype    = 'IOC_SPI',
                                               base     = ioc_base + offset,
                                               size     = ioc_size )

                    archi.addIrq( dstdev  = xcu, 
                                  port    = TODO 
                                  srcdev  = ioc_bak )

                for p in xrange ( nb_cores ):
                    archi.addProc( x, y, p )

            ###  peripherals in external cluster_io 
            if( cluster_xy == io_cxy ):

                tty = archi.addDevice( ptype    = 'TXT_TTY',
                                       base     = tty_base + offset,
                                       size     = tty_size, 
                                       channels = nb_ttys )

                ioc = archi.addDevice( ptype    = ioc_type,
                                       base     = ioc_base + offset,
                                       size     = ioc_size )

                nic = archi.addDevice( ptype    = 'NIC_CBF',
                                       base     = nic_base + offset,
                                       size     = nic_size, 
                                       channels = nb_nics )

                fbf = archi.addDevice( ptype = 'FBF_SCL',
                                       base  = fbf_base + offset,
                                       size  = fbf_size, 
                                       arg0 = fbf_width, arg1 = fbf_width )

                pic = archi.addDevice( 'PIC', base = pic_base + offset, size = pic_size, 
                                         ptype = 'PIC', channels = 32 )

                archi.addIrq( dstdev = pic, port = 0, srcdev = nic, channel = 0 )
# todo
#                archi.addIrq( pic, index = 1, src = nic,
#                                isrtype = 'ISR_NIC_RX', channel = 1 )
#                archi.addIrq( pic, index = 2, src = nic,
#                                isrtype = 'ISR_NIC_TX', channel = 0 )
#                archi.addIrq( pic, index = 3, src = nic,
#                                isrtype = 'ISR_NIC_TX', channel = 1 )
#                archi.addIrq( pic, index = 4, src = cma,
#                                isrtype = 'ISR_CMA', channel = 0 )
#                archi.addIrq( pic, index = 5, src = cma,
#                                isrtype = 'ISR_CMA', channel = 1 )
#                archi.addIrq( pic, index = 6, src = cma,
#                                isrtype = 'ISR_CMA', channel = 2 )
#                archi.addIrq( pic, index = 7, src = cma,
#                                isrtype = 'ISR_CMA', channel = 3 )


                archi.addIrq( dstdev = pic, port = 8, srcdev = ioc )

#                archi.addIrq( pic, index = 16, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 0 )
#                archi.addIrq( pic, index = 17, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 1 )
#                archi.addIrq( pic, index = 18, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 2 )
#                archi.addIrq( pic, index = 19, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 3 )
#                archi.addIrq( pic, index = 20, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 4 )
#                archi.addIrq( pic, index = 21, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 5 )
#                archi.addIrq( pic, index = 22, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 6 )
#                archi.addIrq( pic, index = 23, src = tty,
#                                isrtype = 'ISR_TTY_RX', channel = 7 )

    return archi

########################## platform test #############################################

if __name__ == '__main__':

    archi = Archinfo( x_size    = 2,
                      y_size    = 3,
                      nb_cores  = 2 )

    print archi.xml()

#   print archi.giet_vsegs()


# Local Variables:
# tab-width: 4;
# c-basic-offset: 4;
# c-file-offsets:((innamespace . 0)(inline-open . 0));
# indent-tabs-mode: nil;
# End:
#
# vim: filetype=python:expandtab:shiftwidth=4:tabstop=4:softtabstop=4
