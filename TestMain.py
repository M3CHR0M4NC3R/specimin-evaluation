import unittest
import main
import shutil
import os
from Keyvalue import JsonKeys

class TestMain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #TODO: previously used cf-1291 (index 0) fails when absolute path of the target is used. Will investigate it later. 
        #Currently using cf-6060 
        cls.json_data = main.read_json_from_file('resources/test_data.json')[3]
        sp_env_var = main.get_specimin_env_var()
        if sp_env_var is not None and os.path.exists(sp_env_var) and os.path.isdir(sp_env_var):
            print("Local Specimin copy is being used")
            cls.specimin_dir = sp_env_var
        else:
            print("Local Specimin not found. Cloning a Specimin copy")
            main.clone_repository('https://github.com/kelloggm/specimin.git', 'resources')
            cls.specimin_dir = os.path.abspath("resources/specimin")

    @classmethod
    def tearDownClass(cls):
        # deleting specimin from resources
        try:
            shutil.rmtree('resources/specimin')
        except Exception as e:
            print(f"Error occurred {e}")
        # removing any issue project cloned in resources   
        for root, dirs, files in os.walk('resources', topdown=False):
            for dir_name in dirs:
                if 'cf-' in dir_name:
                    dir_path = os.path.join(root, dir_name)
                    shutil.rmtree(dir_path)
                    print(f"Removed directory: {dir_path}")


    def test_get_repository_name(self):
        url = 'git@github.com:codespecs/daikon.git'
        self.assertEqual(main.get_repository_name(url), 'daikon')

        url = 'git@github.com:kelloggm/specimin.git'
        self.assertEqual(main.get_repository_name(url), 'specimin')

        url = 'git@github.com:typetools/checker-framework.git'
        self.assertEqual(main.get_repository_name(url), 'checker-framework')

        url = 'git@github.com:awslabs/aws-kms-compliance-checker.git'
        self.assertEqual(main.get_repository_name(url), 'aws-kms-compliance-checker')

        url = 'https://github.com/kelloggm/specimin.git'
        self.assertEqual(main.get_repository_name(url), 'specimin')

        url = 'git@github.com:awslabs/aws-kms-compliance-checker.git' 
        self.assertNotEqual(main.get_repository_name(url), 'aws-km-compliance-checker')
    
    def test_build_specimin_command(self):
        proj_name = 'cassandra'
        root = 'src/java'
        targets = [{
                    "method": "getMode(ColumnMetadata, Map<String, String>)",
                    "file": "IndexMode.java",
                    "package": 'org.apache.cassandra.index.sasi.conf',
                    "model": "cf"
                   }]
 
        target_dir = '/user/ISSUES/cf-6077'
        command = main.build_specimin_command(proj_name, target_dir, root, targets)
        target_command = ''
        with open('resources/specimin_command_cf-6077.txt','r') as file:
            target_command = file.read()
        self.assertEqual(command, target_command)
        # not executing since this crashes specimin
        proj_name = 'kafka-sensors'
        root = 'src/main/java/'
        targets = [{
                    "method": "transform(String, byte[])",
                    "file": "Avro2Confluent.java",
                    "package": 'com.fillmore_labs.kafka.sensors.serde.confluent.interop',
                    "model" : "cf"
                   }]

        target_dir = '/user/ISSUES/cf-6019'
        command = main.build_specimin_command(proj_name, target_dir, root, targets)
        with open('resources/specimin_command_cf-6019.txt','r') as file:
            target_command = file.read()
        self.assertEqual(command, target_command)
        #not executing since it crashes specimin.

        # make 
        issue_name = self.json_data[JsonKeys.ISSUE_ID.value]
        main.create_issue_directory('resources', issue_name)
        self.assertTrue(os.path.exists(f'resources/{issue_name}/input'))
        main.clone_repository(self.json_data[JsonKeys.URL.value], f"resources/{issue_name}/input") 

        project_name = main.get_repository_name(self.json_data[JsonKeys.URL.value])
        self.assertTrue(main.checkout_commit(self.json_data[JsonKeys.COMMIT_HASH.value],f"resources/{issue_name}/input/{project_name}"))
        self.assertTrue(main.is_git_directory(f"resources/{issue_name}/input/{project_name}")) 
        main.change_branch(self.json_data[JsonKeys.BRANCH.value], f"resources/{issue_name}/input/{project_name}")

        #build_specimin_command accept absolute path of the root directory.
        command = main.build_specimin_command(project_name, os.path.abspath(f"resources/{issue_name}"), self.json_data[JsonKeys.ROOT_DIR.value], self.json_data[JsonKeys.TARGETS.value])
        print(command)
        result = main.run_specimin(issue_name, command, self.specimin_dir)
        self.assertEqual(result.status, "PASS")
 
    def test_run_specimin(self):
        proj_name = 'test_proj'
        root = ''
        targets = [{
                    "method": "bar()",
                    "file": "Simple.java",
                    "package": "com.example",
                    "model" : "cf"
                   }]
        target_dir = 'resources/onefilesimple'

        command = main.build_specimin_command(proj_name, os.path.abspath(target_dir), root, targets)
        result = main.run_specimin(proj_name, command, self.specimin_dir)
        self.assertEqual(result.status, "PASS")




if __name__ == '__main__':
    unittest.main()
