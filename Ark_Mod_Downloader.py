import arkit
import sys
import os
import argparse
import shutil
import subprocess
from collections import OrderedDict
import struct
import urllib.request
import zipfile
import threading

debug = True

log_dir = os.path.join(os.getcwd(),str(os.times))

def create_log_dir():
    os.makedirs(log_dir)
    
def log(mes,id=1):
    if debug:
        if id==1:
            print('log message: '+mes+'\n')
        else:
            if not os.path.isfile(id):
                open(id, "x")
            with open(id,'a') as file:
                if file.writable():
                    file.write(mes)   
            
class ArkmodDownloader():

    def __init__(self, steamcmd, modids, working_dir, mod_update, modname, preserve=False,multithread=False):
        
        # I not working directory provided, check if CWD has an ARK server.
        self.working_dir = working_dir
        if not working_dir:
            self.working_dir_check()

        self.steamcmd = steamcmd  # Path to SteamCMD exe

        if not self.steamcmd_check():
            print("SteamCMD Not Found And We Were Unable To Download It")
            sys.exit(0)
            
        self.multithread = multithread
        self.modname = modname
        self.installed_Mods = []  # List to hold installed Mods
        self.map_names = []  # Stores map names from mod.info
        self.meta_data = OrderedDict([])  # Stores key value from modmeta.info
        self.preserve = preserve
        self.download_dir = os.path.join(self.working_dir,'.temp_ark_mod_downloader')
        self.temp_mod_path = os.path.join(self.download_dir, r"steamapps", r"workshop", r"content", r"346110")
        self.prep_steamcmd()

        if mod_update:
            print("[+] mod Update Is Selected.  Updating Your Existing Mods")
            self.update_Mods()

        # If any issues happen in download and extract chain this returns false
        if modids:
            successfully_installed_Mods = []
            failed_to_install_Mods = []
            threads =[]
            def download_logic(mod):
                print("\n\n\n\n\n[+] downloading mod " + mod)
                download_dir = self.make_download_dir(mod)
                if self.download_mod(mod,download_dir):
                    successfully_installed_Mods.append(mod)
                else:
                    failed_to_install_Mods.append(mod)
                    print("[x] Error downloading mod " + mod)
                    

            for mod in modids:

                for mod in self.installed_Mods:
                    if self.multithread:
                        t = threading.Thread(target=download_logic, args=(mod,))
                        t.start()
                        threads.append(t)
                    else:
                        download_logic(mod)
                
                for t in threads:
                    t.join()

                for succ_mod in successfully_installed_Mods:
                    print(f'[+] successfully updated mod {succ_mod}')

                for succ_mod in failed_to_install_Mods:
                    print(f'[x] Failed to update mod {succ_mod}')
    
    def make_download_dir(self,modid):## it will add modid to the end of the temp ark mod downloader dir name
        return os.path.join(self.working_dir,f'.temp_ark_mod_downloader_{modid}')

    def make_temp_mod_path(self,download_dir):
        return os.path.join(download_dir, r"steamapps", r"workshop", r"content", r"346110")

    def create_mod_name_txt(self, mod_folder, modid):
        print(os.path.join(mod_folder, self.map_names[0] + " - " + modid + ".txt"))
        with open(os.path.join(mod_folder, self.map_names[0] + ".txt"), "w+") as f:
            f.write(modid)

    def working_dir_check(self):
        print("[!] No working directory provided.  Checking Current Directory")
        print("[!] " + os.getcwd())
        if os.path.isdir(os.path.join(os.getcwd(), "ShooterGame","Content")):
            print("[+] Current Directory Has Ark Server.  Using The Current Directory")
            self.working_dir = os.getcwd()
        else:
            print("[x] Current Directory Does Not Contain An ARK Server. Aborting")
            sys.exit(0)

    def steamcmd_check(self):#it checks for the file called "steamcmd". create a shortcut on windows or a sym link in linux to steamcmd in the working dir
        """
        If SteamCMD path is provided verify that exe exists.
        If no path provided check TCAdmin path working dir.  If not located try to download SteamCMD.
        :return: Bool
        """

        # Check provided directory
        if self.steamcmd:
            print("[+] Checking Provided Path For steamcmd")
            if os.path.isfile(os.path.join(self.steamcmd, "steamcmd")):
                self.steamcmd = os.path.join(self.steamcmd, "steamcmd")
                print("[+] steamcmd Found At Provided Path")
                return True

        # Check working directory
        if os.path.isfile(os.path.join(self.working_dir, "steamcmd")):
            print("[+] Located steamcmd")
            self.steamcmd = os.path.join(self.working_dir, "steamcmd")
            return True

        return False

    def prep_steamcmd(self):
        return

    def update_Mods(self):
        self.build_list_of_Mods()
        successfully_installed_Mods = []
        failed_to_install_Mods = []

        def download_logic(mod):
            print("\n\n\n\n\n[+] Updating mod " + mod)
            download_dir = self.make_download_dir(mod)
            if self.download_mod(mod,download_dir):
                successfully_installed_Mods.append(mod)
            else:
                failed_to_install_Mods.append(mod)
                print("[x] Error Updating mod " + mod)

        if self.installed_Mods:
            threads =[]
            for mod in self.installed_Mods:
                if self.multithread:
                    t = threading.Thread(target=download_logic, args=(mod,))
                    t.start()
                    threads.append(t)
                else:
                    download_logic(mod)
            
            for t in threads:
                t.join()

            for succ_mod in successfully_installed_Mods:
                print(f'[+] successfully updated mod {succ_mod}')

            for succ_mod in failed_to_install_Mods:
                print(f'[x] Failed to update mod {succ_mod}')
        else:
            print("[+] No Installed Mods Found.  Skipping Update")


    def build_list_of_Mods(self):
        """
        Build a list of all installed Mods by grabbing all directory names from the mod folder
        :return:
        """
        if not os.path.isdir(os.path.join(self.working_dir, "ShooterGame", "Content" , "Mods")):
            print('[!] no Mods directory found')
            return
        for curdir, dirs, files in os.walk(os.path.join(self.working_dir, "ShooterGame", "Content" , "Mods")):
            for d in dirs:
                if d == '111111111':
                    continue
                if d.isdigit():# check if it only contains digits so it doesn't try to download a map
                    self.installed_Mods.append(d)
            break

    def download_mod(self, modid,download_dir,preserve=False):
        preserve = preserve or self.preserve
        if os.path.isdir(download_dir) and not self.preserve:
            shutil.rmtree(download_dir)
        """
        Launch SteamCMD to download modID
        :return:
        """
        
        print("[+] Starting Download of mod " + str(modid))
        args = []
        args.append(self.steamcmd)
        args.append(f"+force_install_dir {download_dir}") # added this to get a cleaner download.
        args.append("+login anonymous")
        args.append("+workshop_download_item")
        args.append("346110")
        args.append(modid)
        if preserve:
            args.append("validate")
        args.append("+quit")
        
        output = str(subprocess.run(args, shell=False, stdout=subprocess.PIPE).stdout.decode('utf-8'))
        
        if not 'Success. Downloaded item' in output:
            return self.download_mod(modid,download_dir,True)
        if not os.path.isdir(download_dir):# checks if steamcmd made the download_dir if not then it failed to download
            log('failed to download mod with steamcmd | aborting mod download')
            return False
        success = True if self.extract_mod(modid,download_dir) else False
        if os.path.isdir(download_dir) and not self.preserve: # remove the download_dir to get a clean download next time. if preserve is true it won't delete it
            shutil.rmtree(download_dir)
        return success


    def extract_mod(self, modid,download_dir):
        """
        Extract the .z files using the arkit lib.
        If any file fails to download this whole script will abort
        :return: None
        """

        print("[+] Extracting .z Files.")

        try:
            for curdir, subdirs, files in os.walk(os.path.join(self.make_temp_mod_path(download_dir), modid, "WindowsNoEditor")):
                for file in files:
                    name, ext = os.path.splitext(file)
                    if ext == ".z":
                        src = os.path.join(curdir, file)
                        dst = os.path.join(curdir, name)
                        uncompressed = os.path.join(curdir, file + ".uncompressed_size")
                        arkit.unpack(src, dst)
                        #print("[+] Extracted " + file)
                        os.remove(src)
                        if os.path.isfile(uncompressed):
                            os.remove(uncompressed)

        except (arkit.UnpackException, arkit.SignatureUnpackException, arkit.CorruptUnpackException) as e:
            print("[x] Unpacking .z files failed, aborting mod install")
            log(e)
            return False

        if self.create_mod_file(modid,download_dir):
            if self.move_mod(modid,download_dir):
                return True
            else:
                log('failed to move mod')
                return False


    def move_mod(self, modid,download_dir):
        """
        Move mod from SteamCMD download location to the ARK server.
        It will delete an existing mod with the same ID
        :return:
        """

        ark_mod_folder = os.path.join(self.working_dir, "ShooterGame","Content", "Mods")
        output_dir = os.path.join(ark_mod_folder, str(modid))
        source_dir = os.path.join(self.make_temp_mod_path(download_dir), modid, "WindowsNoEditor")

        # TODO Need to handle exceptions here   
        if not os.path.isdir(ark_mod_folder):
            print("[+] Creating Directory: " + ark_mod_folder)
            os.mkdir(ark_mod_folder)

        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

        print("[+] Moving mod Files To: " + output_dir)
        shutil.copytree(source_dir, output_dir)

        if self.modname:
            print("Creating mod Name File")
            self.create_mod_name_txt(ark_mod_folder, modid)

        old_name = os.path.join(self.working_dir, "ShooterGame","Content", "Mods",modid,".mod")
        new_name = os.path.join(self.working_dir, "ShooterGame","Content", "Mods",modid,f"{modid}.mod")
        new_path = os.path.join(self.working_dir, "ShooterGame","Content", "Mods",f"{modid}.mod")# is the final location. is used to check if the file is there and if it is there remove it
        if os.path.isfile(old_name):
            os.rename(old_name, new_name)# change .mod file name to {modid}.mod
            if os.path.isfile(new_path):# check if it already exists
                os.remove(new_path)
            shutil.move(new_name, ark_mod_folder)
        return True

    def create_mod_file(self, modid,download_dir):
        """
        Create the .mod file.
        This code is an adaptation of the code from Ark Server Launcher.  All credit goes to Face Wound on Steam
        :return:
        """
        if not self.parse_base_info(modid,download_dir) or not self.parse_meta_data(modid,download_dir):
            return False

        print("[+] Writing .mod File")
        with open(os.path.join(self.make_temp_mod_path(download_dir), modid, r"WindowsNoEditor", r".mod"), "w+b") as f:

            modid = int(modid)

            f.write(struct.pack('Ixxxx', modid))  # Needs 4 pad bits
            self.write_ue4_string("modName", f)
            self.write_ue4_string("", f)

            map_count = len(self.map_names)
            f.write(struct.pack("i", map_count))

            for m in self.map_names:
                self.write_ue4_string(m, f)

            # Not sure of the reason for this
            num2 = 4280483635
            f.write(struct.pack('I', num2))
            num3 = 2
            f.write(struct.pack('i', num3))

            if "modType" in self.meta_data:
                mod_type = b'1'
            else:
                mod_type = b'0'

            # TODO The packing on this char might need to be changed
            f.write(struct.pack('p', mod_type))
            meta_length = len(self.meta_data)
            f.write(struct.pack('i', meta_length))

            for k, v in self.meta_data.items():
                self.write_ue4_string(k, f)
                self.write_ue4_string(v, f)

        return True

    def read_ue4_string(self, file):
        count = struct.unpack('i', file.read(4))[0]
        flag = False
        if count < 0:
            flag = True
            count -= 1

        if flag or count <= 0:
            return ""

        return file.read(count)[:-1].decode()

    def write_ue4_string(self, string_to_write, file):
        string_length = len(string_to_write) + 1
        file.write(struct.pack('i', string_length))
        barray = bytearray(string_to_write, "utf-8")
        file.write(barray)
        file.write(struct.pack('p', b'0'))

    def parse_meta_data(self, modid,download_dir):
        """
        Parse the modmeta.info files and extract the key value pairs need to for the .mod file.
        How To Parse modmeta.info:
            1. Read 4 bytes to tell how many key value pairs are in the file
            2. Read next 4 bytes tell us how many bytes to read ahead to get the key
            3. Read ahead by the number of bytes retrieved from step 2
            4. Read next 4 bytes to tell how many bytes to read ahead to get value
            5. Read ahead by the number of bytes retrieved from step 4
            6. Start at step 2 again
        :return: Dict
        """

        print("[+] Collecting mod Meta Data From modmeta.info")
        print("[+] Located The Following Meta Data:")

        mod_meta = os.path.join(self.make_temp_mod_path(download_dir), modid, r"WindowsNoEditor", r"modmeta.info")
        if not os.path.isfile(mod_meta):
            print("[x] Failed To Locate modmeta.info. Cannot continue without it.  Aborting")
            return False

        with open(mod_meta, "rb") as f:

            total_pairs = struct.unpack('i', f.read(4))[0]

            for i in range(total_pairs):

                key, value = "", ""

                key_bytes = struct.unpack('i', f.read(4))[0]
                key_flag = False
                if key_bytes < 0:
                    key_flag = True
                    key_bytes -= 1

                if not key_flag and key_bytes > 0:

                    raw = f.read(key_bytes)
                    key = raw[:-1].decode()

                value_bytes = struct.unpack('i', f.read(4))[0]
                value_flag = False
                if value_bytes < 0:
                    value_flag = True
                    value_bytes -= 1

                if not value_flag and value_bytes > 0:
                    raw = f.read(value_bytes)
                    value = raw[:-1].decode()

                # TODO This is a potential issue if there is a key but no value
                if key and value:
                    print("[!] " + key + ":" + value)
                    self.meta_data[key] = value

        return True


    def parse_base_info(self, modid,download_dir):

        print("[+] Collecting mod Details From mod.info")

        mod_info = os.path.join(self.make_temp_mod_path(download_dir), modid, r"WindowsNoEditor", r"mod.info")

        if not os.path.isfile(mod_info):
            print("[x] Failed to locate mod.info. Cannot Continue.  Aborting")
            return False

        with open(mod_info, "rb") as f:
            self.read_ue4_string(f)
            map_count = struct.unpack('i', f.read(4))[0]

            for i in range(map_count):
                cur_map = self.read_ue4_string(f)
                if cur_map:
                    self.map_names.append(cur_map)

        return True



def main():
    parser = argparse.ArgumentParser(description="A utility to download ARK Mods via SteamCMD")
    parser.add_argument("--workingdir", default=None, dest="workingdir", help="Game server home directory.  Current Directory is used if this is not provided")
    parser.add_argument("--modids", nargs="+", default=None, dest="modids", help="ID of mod To Download")
    parser.add_argument("--steamcmd", default=None, dest="steamcmd", help="Path to SteamCMD")
    parser.add_argument("--update", default=None, action="store_true", dest="mod_update", help="Update Existing Mods.  ")
    parser.add_argument("--preserve", default=None, action="store_true", dest="preserve", help="Don't Delete steamcmd Content Between Runs")
    parser.add_argument("--namefile", default=None, action="store_true", dest="modname", help="Create a .name File With Mods Text Name")
    parser.add_argument("--multithread", default=None, action="store_true", dest="multithread", help="multithread the download of mods so it is faster")
    args = parser.parse_args()

    if not args.modids and not args.mod_update:
        print("[x] No mod ID Provided and Update Not Selected.  Aborting")
        print("[?] Please provide a mod ID to download or use --update to update your existing Mods")
        sys.exit(0)

    ArkmodDownloader(args.steamcmd,
                     args.modids,
                     args.workingdir,
                     args.mod_update,
                     args.modname,
                     args.preserve,
                     args.multithread)



if __name__ == '__main__':
    main()
