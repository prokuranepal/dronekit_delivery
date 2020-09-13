import unittest
from sendData import on_mission_download, update_mission, vehicle,  set_mode_RTL, on_initiate_flight, set_mode_LAND
import time



class TestSendData(unittest.TestCase):
    def test_on_mission_download(self):
        p_koteshwor={0: {'lat': -35.36199188232422, 'lng': 149.16159057617188, 'alt': 10.0, 'command': 16}, 1: {'lat': -35.36381149291992, 'lng': 149.16160583496094, 'alt': 10.0, 'command': 16}, 2: {'lat': -35.36376953125, 'lng': 149.16305541992188, 'alt': 10.0, 'command': 16}, 3: {'lat': -35.36183547973633, 'lng': 149.1630096435547, 'alt': 10.0, 'command': 16}, 4: {'lat': -35.36214828491211, 'lng': 149.16204833984375, 'alt': 10.0, 'command': 16}}
        # self.assertIsNotNone(on_mission_download('kkk'))
        update_mission("jt601Koteshwor.txt")
        self.assertIsNotNone(on_mission_download('kkk'))
        self.assertDictEqual(on_mission_download(3),p_koteshwor)
        # update_mission("jt601Nangi.txt")
        # self.assertDictEqual(on_mission_download(4),p_koteshwor)
    def test_update_mission(self):
        # time.sleep(5)
        p_koteshwor1={0: {'lat': -35.36199188232422, 'lng': 149.16159057617188, 'alt': 10.0, 'command': 16}, 1: {'lat': -35.36381149291992, 'lng': 149.16160583496094, 'alt': 10.0, 'command': 16}, 2: {'lat': -35.36376953125, 'lng': 149.16305541992188, 'alt': 10.0, 'command': 16}, 3: {'lat': -35.36183547973633, 'lng': 149.1630096435547, 'alt': 10.0, 'command': 16}, 4: {'lat': -35.36214828491211, 'lng': 149.16204833984375, 'alt': 10.0, 'command': 16}}
        # self.assertFalse(update_mission("jt601Koteshwor.txt"))
        update_mission("jt601Koteshwor.txt")
        d = on_mission_download(2)
        self.assertDictEqual(d,p_koteshwor1)
        # update_mission("jt601Nangi.txt")
        # self.assertDictEqual(on_mission_download(4),p_koteshwor)
    def test_on_initiate_flight(self):
        time.sleep(3)
        update_mission("jt601Koteshwor.txt")
        mode, armed = on_initiate_flight(5)

        # update_mission("jt601Nangi.txt")
        self.assertEqual(mode, "AUTO")
        self.assertTrue(armed)
        mode2, armed2 = on_initiate_flight(5)
        self.assertEqual(mode2, "AUTO")
        self.assertTrue(armed2)

        time.sleep(5)
    

    def test_set_mode_RTL(self):
        time.sleep(3)

        print ("fix type",vehicle.gps_0.fix_type)
        if vehicle.gps_0.fix_type>1:
            self.assertEqual(set_mode_RTL(3),"RTL")
        else:
            self.assertEqual(set_mode_RTL(3),"STABILIZE")
        # update_mission("jt601Nangi.txt")
        # self.assertDictEqual(on_mission_download(4),p_koteshwor)
        time.sleep(3)


    def test_set_mode_LAND(self):
        time.sleep(3)

        print ("fix type",vehicle.gps_0.fix_type)
        if vehicle.gps_0.fix_type>1:
            self.assertEqual(set_mode_LAND(3),"LAND")
        else:
            self.assertEqual(set_mode_LAND(3),"STABILIZE")

        # update_mission("jt601Nangi.txt")
        # self.assertDictEqual(on_mission_download(4),p_koteshwor)
        time.sleep(3)




if __name__ == '__main__':
    # unittest.main()
    runner = unittest.TextTestRunner()
    itersuite = unittest.TestLoader().loadTestsFromTestCase(TestSendData)
    runner.run(itersuite)