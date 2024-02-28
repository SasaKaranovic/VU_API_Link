# pylint: disable=pointless-string-statement
import os
import sys
import getpass
from vu_notifications import show_error_msg

'''
VU Server file system class

This class determines base directory for all files/paths consumed by VU Server.
It also provides a way for user/system to specify where VU Server should store data.

Note: All data files will be placed on a same/shared path.
Data files might be separated into subdirectories where it makes sense.

Base directory is defined from on of the following:

    First: System Environment Variable `VU_SERVER_DATA_PATH`
            Requirement: path is valid/exists and is writable by current process

    Second: Current user home directory
            Windows : c:/Users/USERNAME/KaranovicResearch
            Linux   : /home/USERNAME/KaranovicResearch
            Mac Os  : /Users/USERNAME/Library/KaranovicResearch
            Requirement: Path is writable by current process

    Last: VU Server install directory
            This is last-resort for storing VU server data.
            Note that application data will get removed if install directory is removed.

Transition fix:
    This change breaks current app behaviour. In order to prevent data loss and offer
    seamless transition, this class will try to migrate (copy) data from old paths
    and also mark the old files as `_migrated` (instead of removing).

'''
class FileSystem:
    base_path = None

    def __init__(self):
        potential_paths = [ os.environ.get('VU_SERVER_DATA_PATH', None),
                            self._get_user_directory(),
                            self._get_app_directory() ]

        for test_path in potential_paths:
            print(f"Testing path: {test_path}")
            if self._is_useable_path(test_path):
                self.base_path = os.path.join(test_path, 'KaranovicResearch', 'APILink')
                break

        if self.base_path is None:
            print(f"Tested paths: {potential_paths}")
            print("Could not find useable directory for VU Server data!")
            print("Please make sure VU Server application is running with administrative privileges!")
            show_error_msg("File System Error!",
                           "Could not find useable directory for VU Server data!\n"
                           "Please make sure VU Server application is running with administrative privileges!")
            sys.exit(-1)
            # We can abort and shut-down gracefully here
            # Or try to run and pray for a miracle

        # Create required directories and files
        self._create_default_directories()
        self._create_empty_config_file()

    def _get_user_directory(self):
        # Linux
        if sys.platform in ["linux", "linux2"]:
            return f'/home/{getpass.getuser()}'

        # MacOS
        if sys.platform == "darwin":
            return '~/Library'

        # Windows
        if sys.platform == "win32":
            return os.path.join(os.path.expanduser(os.getenv('USERPROFILE')))
        return None

    def _get_app_directory(self):
        return os.path.abspath(os.path.dirname(__file__))


    def _is_useable_path(self, test_path):
        if test_path is None:
            return False

        try:
            os.makedirs(test_path, exist_ok=True)
            if not os.path.isdir(test_path):
                print(f"{test_path} is not directory!")
                return False

            return self._is_writeable_path(test_path)
        except OSError as error:
            show_error_msg("Error while creating path!", f"Could not create`{test_path}`.\n{error}")
            print("Error while creating path!")
            print(error)
            return False

        return False

    def _is_writeable_path(self, test_path):
        try:
            # Create test file
            test_file = os.path.join(test_path, 'tmp.txt')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('ok')

            # Remove test file
            os.remove(test_file)

            # By this point we should assume read/write access
            return True
        except Exception as e:
            print(e)
        return False

    def _create_default_directories(self):
        os.makedirs(os.path.dirname(self.get_log_file_path()), exist_ok=True)
        os.makedirs(self.get_upload_directory_path(), exist_ok=True)
        os.makedirs(self.get_links_folder_path(), exist_ok=True)
        os.makedirs(self.get_link_images_folder_path(), exist_ok=True)

    def _create_empty_config_file(self):
        if not os.path.isfile(self.get_config_file_path()):
            with open(self.get_config_file_path(), 'w', encoding='utf-8') as f:
                f.write('server:\n')
                f.write('  hostname: localhost\n')
                f.write('  port: 5340\n')
                f.write('  communication_timeout: 10\n')
                f.write('  dial_update_period: 200\n')
                f.write('  master_key: cTpAWYuRpA2zx75Yh961Cg\n')
                f.write('\n')
                f.write('hardware:\n')
                f.write('  port: \n')
                f.write('\n')
    def get_image_list(self):
        ret = []
        images = os.listdir(self.get_link_images_folder_path())
        images = [item for item in images if item.endswith('.png')]

        for img in images:
            ret.append(img)

        return ret

    def get_www_folder_path(self):
        return os.path.join(os.path.dirname(__file__), 'www')

    def get_log_file_path(self):
        return os.path.join(self.base_path, 'server.log')

    def get_links_folder_path(self):
        return os.path.join(self.base_path, 'links')

    def get_link_images_folder_path(self):
        return os.path.join(self.get_links_folder_path(), 'images')

    def get_config_file_path(self):
        return os.path.join(self.base_path, 'config.yaml')

    def get_upload_directory_path(self):
        return os.path.join(self.base_path, 'upload')

VU_FileSystem = FileSystem()


if __name__ == '__main__':
    vfs = FileSystem()

    print(vfs.get_www_folder_path())
    print(vfs.get_log_file_path())
    print(vfs.get_links_folder_path())
    print(vfs.get_config_file_path())
    print(vfs.get_upload_directory_path())
