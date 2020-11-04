from lib.mining_utils import has_Source_Extension, is_Test, is_Valid_Key, filter_top_frequent_words, extract_Keys
import unittest



class TestMiningUtils(unittest.TestCase):
    def test_has_Source_Extension(self):
        test_list = ["test.py", "test.c", "test.java", "test", "test.test"]
        for i in range(len(test_list)):
            if i < 3:
                self.assertTrue(has_Source_Extension(test_list[i]))
            else:
                self.assertFalse(has_Source_Extension(test_list[i]))

    def test_is_Test(self):
        path_list = ["/src/test/test.py", "test/test.py", "/src/main.py"]

        for i in range(len(path_list)):
            if i < 2:
                self.assertTrue(is_Test(path_list[i]))
            else:
                self.assertFalse(is_Test(path_list[i]))


    def test_filter_top_frequent_words(self):
        text = "home sweet home, sweet home alabama, there is no place like home"

        self.assertEqual(filter_top_frequent_words(text), "home:4 sweet:2 alabama:1 place:1 like:1")

    def test_extract_Keys(self):
        texto = 'CONTRIBUTED BY MUKUND THAKUR \
        HDFS-15253 DEFAULT CHECKPOINT TRANSFER SPEED, 50MB PER SECOND (#2366) \
        HDFS-15610 REDUCED DATANODE UPGRADE/HARDLINK THREAD FROM 12 TO 6 (#2365) \
        HADOOP-17021. ADD CONCAT FS COMMAND (#1993)'

        self.assertEqual(extract_Keys(texto), ['HDFS-15253', 'HDFS-15610', 'HADOOP-17021'])


    def test_is_Valid_Key(self):
        keys_list = ['HDFS-15613', 'HDFS-14442', 'HDFS-15543', '7345-chave', 'key123', 'test_key']

        for i in range(len(keys_list)):
            if i < 3:
                self.assertTrue(is_Valid_Key(keys_list[i]))
            else:
                self.assertFalse(is_Valid_Key(keys_list[i]))

if __name__ == "__main__":
    unittest.main()
