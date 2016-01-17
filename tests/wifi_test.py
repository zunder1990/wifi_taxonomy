#!/usr/bin/python
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for taxonomy/wifi.py."""

__author__ = 'dgentry@google.com (Denton Gentry)'


import unittest
import dhcp
import wifi


class WifiTaxonomyTest(unittest.TestCase):

  def setUp(self):
    dhcp.DHCP_LEASES_FILE = 'testdata/dhcp.leases'
    dhcp.DHCP_SIGNATURE_FILE = 'testdata/dhcp.signatures'

  def testLookup(self):
    signature = ('wifi|probe:0,1,50,45,htcap:186e|assoc:0,1,50,48,'
                 '221(0050f2,2),45,127,htcap:086c,htmcs:000000ff')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual(3, len(taxonomy))
    self.assertEqual('RTL8192CU', taxonomy[0])
    self.assertEqual('802.11n n:1,w:20', taxonomy[2])

    signature = ('wifi3|probe:0,1,45,221(00904c,51),htcap:09ef,htagg:1b,'
        'htmcs:0000ffff|assoc:0,1,33,36,48,45,221(00904c,51),221(0050f2,2),'
        'cap:0011,htcap:09ef,htagg:1b,htmcs:0000ffff,txpow:0005')
    taxonomy = wifi.identify_wifi_device(signature, '3c:15:c2:00:00:01')
    expected = 'BCM4331;MacBook Pro 17" late 2011 (A1297);802.11n n:2,w:40'
    self.assertEqual(';'.join(taxonomy), expected)
    self.assertEqual(3, len(taxonomy))
    self.assertEqual('BCM4331', taxonomy[0])
    self.assertEqual('MacBook Pro 17" late 2011 (A1297)', taxonomy[1])
    self.assertEqual('802.11n n:2,w:40', taxonomy[2])

  def testNameLookup(self):
    signature = 'wifi3|probe:0,1,3,50|assoc:0,1,48,50,cap:0411'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual(3, len(taxonomy))
    self.assertEqual('Unknown', taxonomy[1])
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual(3, len(taxonomy))
    self.assertEqual('Unknown', taxonomy[1])
    taxonomy = wifi.identify_wifi_device(signature, '2c:1f:23:ff:ff:01')
    self.assertEqual('iPod Touch 1st/2nd gen', taxonomy[1])

  def testChecksumWhenNoIdentification(self):
    taxonomy = wifi.identify_wifi_device('wifi|probe:1,2,3,4,htcap:0|assoc:1',
                                         '00:00:01:00:00:01')
    h = 'SHA:27b78dbb1bc795961ddad0686137eb9fddbbc7f8766bd8947b4deca563b830be'
    self.assertIn(h, taxonomy[0])

  def testOUI(self):
    # Devices with a generic signature, distinguished via MAC OUI
    signature = ('wifi|probe:0,1,50,45,3,221(001018,2),221(00904c,51),'
                 'htcap:110c,htagg:19,htmcs:000000ff|assoc:0,1,48,50,45,'
                 '221(001018,2),221(00904c,51),221(0050f2,2),htcap:110c,'
                 'htagg:19,htmcs:000000ff')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertIn('Unknown', taxonomy[1])
    taxonomy = wifi.identify_wifi_device(signature, '00:24:e4:00:00:01')
    self.assertIn('Withings', taxonomy[1])
    taxonomy = wifi.identify_wifi_device(signature, 'ac:22:0b:00:00:01')
    self.assertIn('Nexus 7', taxonomy[1])

    # Test one of the OUIs with multiple vendors listed.
    signature = ('wifi|probe:0,1,3,45,50,htcap:0120,htagg:03,htmcs:00000000|'
                 'assoc:0,1,48,50,127,221(0050f2,2),45,htcap:012c,htagg:03,'
                 'htmcs:000000ff,extcap:00000000|oui:google')
    taxonomy = wifi.identify_wifi_device(signature, '6c:ad:f8:00:00:01')
    self.assertEqual('Chromecast', taxonomy[1])

  def testOS(self):
    signature = 'wifi|probe:0,1,50|assoc:0,1,50,48,221(0050f2,2)'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertIn('Unknown', taxonomy[1])
    taxonomy = wifi.identify_wifi_device(signature, '28:ef:01:00:00:01')
    self.assertIn('Kindle', taxonomy[1])

  def testUnknown(self):
    signature = 'wifi|probe:0,1,2,vhtcap:0033|assoc:3,4,vhtcap:0033'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertIn('802.11ac', taxonomy[2])
    self.assertNotIn('802.11n', taxonomy[2])
    self.assertNotIn('802.11a/b/g', taxonomy[2])
    signature = 'wifi|probe:0,1,2,htcap:0033|assoc:3,4,htcap:0033'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertNotIn('802.11ac', taxonomy[2])
    self.assertIn('802.11n', taxonomy[2])
    self.assertNotIn('802.11a/b/g', taxonomy[2])
    signature = 'wifi|probe:0,1,2|assoc:3,4'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertNotIn('802.11ac', taxonomy[2])
    self.assertNotIn('802.11n', taxonomy[2])
    self.assertIn('802.11a/b/g', taxonomy[2])

  def test802_11n_NssWidth(self):
    signature = 'wifi|probe:0|assoc:1,htcap:012c,htagg:03,htmcs:000000ff'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:1,w:20', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,htcap:0102,htagg:03,htmcs:0000ffff'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:2,w:40', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,htcap:0200,htagg:03,htmcs:00ffffff'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:3,w:20', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,htcap:0302,htagg:03,htmcs:ffffffff'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:4,w:40', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11a/b/g n:1,w:20', taxonomy[2])

  def test802_11ac_Width(self):
    signature = ('wifi|probe:0|assoc:1,htcap:0302,htmcs:000000ff,'
                 'vhtcap:00000000,vhtrxmcs:0000ffaa,vhttxmcs:0000ffaa')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:4,w:80', taxonomy[2])
    signature = ('wifi|probe:0|assoc:1,htcap:0200,htmcs:000000ff,'
                 'vhtcap:00000004,vhtrxmcs:0000ffea,vhttxmcs:0000ffea')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:3,w:160', taxonomy[2])
    signature = ('wifi|probe:0|assoc:1,htcap:0200,htmcs:000000ff,'
                 'vhtcap:00000004,vhtrxmcs:0000fffa,vhttxmcs:0000fffa')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:2,w:160', taxonomy[2])
    signature = ('wifi|probe:0|assoc:1,htcap:0200,htmcs:000000ff,'
                 'vhtcap:00000004,vhtrxmcs:0000fffe,vhttxmcs:0000fffe')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:1,w:160', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,vhtcap:00000008'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:?,w:80+80', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,vhtcap:0000000c'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11ac n:?,w:??', taxonomy[2])

  def testPerformanceInfoBroken(self):
    signature = ('wifi|probe:0,htmcs:000000ff|assoc:0,htmcs:000000ff')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11a/b/g n:1,w:20', taxonomy[2])
    signature = ('wifi|probe:0,htcap:wrong,htmcs:ffffffff|'
                 'assoc:0,htcap:wrong,htmcs:ffffffff')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:4,w:??', taxonomy[2])
    signature = ('wifi|probe:0,htcap:012c,htmcs:wrong|'
                 'assoc:0,htcap:012c,htmcs:wrong')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:?,w:20', taxonomy[2])
    signature = ('wifi|probe:0,htcap:wrong,htmcs:wrong|'
                 'assoc:0,htcap:wrong,htmcs:wrong')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:?,w:??', taxonomy[2])

  def testRealClientsPerformance(self):
    """Test the performance information for a few real clients."""
    # Nest Thermostat
    sig = ('wifi|probe:0,1,50,45,htcap:0130,htagg:18,htmcs:000000ff|assoc:'
           '0,1,50,48,45,221(0050f2,2),htcap:013c,htagg:18,htmcs:000000ff')
    taxonomy = wifi.identify_wifi_device(sig, '18:b4:30:00:00:01')
    self.assertEqual('802.11n n:1,w:20', taxonomy[2])
    # Samsung Galaxy S4
    sig = (
        'wifi|probe:0,1,45,127,191,221(001018,2),221(00904c,51),221(00904c,'
        '4),221(0050f2,8),htcap:006f,htagg:17,htmcs:000000ff,vhtcap:0f805832,'
        'vhtrxmcs:0000fffe,vhttxmcs:0000fffe|assoc:0,1,33,36,48,45,127,191,'
        '221(001018,2),221(00904c,4),221(0050f2,2),htcap:006f,htagg:17,htmcs:'
        '000000ff,vhtcap:0f805832,vhtrxmcs:0000fffe,vhttxmcs:0000fffe')
    taxonomy = wifi.identify_wifi_device(sig, 'cc:3a:61:00:00:01')
    self.assertEqual('802.11ac n:1,w:80', taxonomy[2])
    # MacBook Pro 802.11ac
    sig = (
        'wifi|probe:0,1,45,127,191,221(00904c,51),htcap:09ef,htagg:17,'
        'htmcs:0000ffff,vhtcap:0f8259b2,vhtrxmcs:0000ffea,vhttxmcs:0000ffea|'
        'assoc:0,1,33,36,48,45,127,191,221(00904c,51),221(0050f2,2),htcap:09ef,'
        'htagg:17,htmcs:0000ffff,vhtcap:0f8259b2,vhtrxmcs:0000ffea,'
        'vhttxmcs:0000ffea')
    taxonomy = wifi.identify_wifi_device(sig, '3c:15:c2:00:00:01')
    self.assertEqual('802.11ac n:3,w:80', taxonomy[2])

  def testBrokenNssWidth(self):
    """Test for broken client behavior.

    A few clients, notably Nexus 4 with Android 4.2,
    include a VHT Capabilities in their Probe even
    though they are not 802.11ac devices. Presumably
    the driver supports other chipsets which are.
    To work around this, taxonomy is only supposed to
    look at the Association for determining client
    performance characteristics.
    """
    signature = ('wifi|probe:0,1,50,45,221(0050f2,8),191,221(0050f2,4),'
                 '221(506f9a,9),htcap:012c,htagg:03,htmcs:000000ff,'
                 'vhtcap:31811120,vhtrxmcs:01b2fffc,vhttxmcs:01b2fffc,'
                 'wps:Nexus_4|assoc:0,1,50,48,45,221(0050f2,2),'
                 'htcap:012c,htagg:03,htmcs:000000ff')
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertEqual('802.11n n:1,w:20', taxonomy[2])

  def testCorruptFiles(self):
    signature = 'wifi|probe:0|assoc:1,htcap:this_is_not_a_number'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertIn('802.11n', taxonomy[2])
    signature = 'wifi|probe:0|assoc:1,vhtcap:this_is_not_a_number'
    taxonomy = wifi.identify_wifi_device(signature, '00:00:01:00:00:01')
    self.assertIn('802.11ac', taxonomy[2])

  def testV1Signature(self):
    sig = ('wifi|probe:0,1,50,45,221(0050f2,8),221(0050f2,4),221(506f9a,9),'
           'htcap:012c,htagg:03,htmcs:000000ff,wps:Nexus_4|assoc:0,1,50,48,45,'
           '221(0050f2,2),htcap:012c,htagg:03,htmcs:000000ff')
    expected = (
        'wifi|probe:0,1,50,45,221(0050f2,8),221(0050f2,4),221(506f9a,9),'
        'htcap:012c,wps:Nexus_4|assoc:0,1,50,48,45,221(0050f2,2),htcap:012c')
    v1 = wifi.make_v1_signature(sig)
    self.assertEqual(v1, expected)
    sig = ('wifi|probe:0,1,45,127,191,221(001018,2),221(00904c,51),'
           '221(00904c,4),221(0050f2,8),htcap:006f,htagg:17,htmcs:000000ff,'
           'vhtcap:0f805832,vhtrxmcs:0000fffe,vhttxmcs:0000fffe|assoc:0,1,33,'
           '36,48,45,127,191,221(001018,2),221(00904c,4),221(0050f2,2),'
           'htcap:006f,htagg:17,htmcs:000000ff,vhtcap:0f805832,'
           'vhtrxmcs:0000fffe,vhttxmcs:0000fffe')
    expected = ('wifi|probe:0,1,45,127,191,221(001018,2),221(00904c,51),'
                '221(00904c,4),221(0050f2,8),htcap:006f,vhtcap:0f805832|assoc:'
                '0,1,33,36,48,45,127,191,221(001018,2),221(00904c,4),'
                '221(0050f2,2),htcap:006f,vhtcap:0f805832')
    v1 = wifi.make_v1_signature(sig)
    self.assertEqual(v1, expected)

  def testV2Signature(self):
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,cap:0123,htcap:012c,txpow:3210'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,htcap:012c'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,extcap:0123456789abcdef'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,extcap:67452301'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)
    # iPhone 6s signature
    sig = ('wifi3|probe:0,1,50,3,45,127,107,221(0050f2,8),221(001018,2),'
           'htcap:002d,htagg:17,htmcs:0000ffff,intwrk:0f,'
           'extcap:0400088400000040|assoc:0,1,50,33,36,48,45,127,221(001018,2),'
           '221(0050f2,2),cap:0431,htcap:002d,htagg:17,htmcs:0000ffff,'
           'txpow:1202,extcap:0000000000000040|os:ios')
    exp = ('wifi|probe:0,1,50,3,45,127,107,221(0050f2,8),221(001018,2),'
           'htcap:002d,htagg:17,htmcs:0000ffff,intwrk:0f,'
           'extcap:84080004|assoc:0,1,50,33,36,48,45,127,221(001018,2),'
           '221(0050f2,2),htcap:002d,htagg:17,htmcs:0000ffff,'
           'extcap:00000000|os:ios')
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)

  def testV2SignatureSmallExtcap(self):
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,extcap:01234567'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,extcap:67452301'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,extcap:012345'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,extcap:452301'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,extcap:0123'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,extcap:2301'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)
    sig = 'wifi3|probe:0,1,50|assoc:0,1,50,extcap:01'
    exp = 'wifi|probe:0,1,50|assoc:0,1,50,extcap:01'
    v2 = wifi.make_v2_signature(sig)
    self.assertEqual(v2, exp)


if __name__ == '__main__':
  unittest.main()