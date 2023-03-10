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
from time import gmtime, strftime
from subprocess import Popen, PIPE

debug = True

time = strftime("%Y-%m-%d--%H-%M-%S", gmtime())
log_dir = os.path.join(os.getcwd(),str(time))
temp_steamcmd_dir_name = '.temp_ark_mod_downloader_steamcmd'


def create_log_dir():
    os.makedirs(log_dir)

if debug:
    create_log_dir()

def log(mes,id=1):
    if debug:
        if id==1:
            print('log message: '+mes)
        else:
            print(mes)
            log_file = os.path.join(log_dir,id)
            if not os.path.isfile(log_file):
                open(log_file, "x")
            with open(log_file,'a') as file:
                if file.writable():
                    file.write(mes)   

is_windows = (os.name == 'nt')

class ArkmodDownloader():

    def __init__(self, steamcmd, modids, working_dir, mod_update, modname, preserve=False,multithread=False,multithread_extraction=False):
        
        # I not working directory provided, check if CWD has an ARK server.

        self.working_dir = working_dir
        if not working_dir:
            self.working_dir_check()

        self.steamcmd = steamcmd  # Path to SteamCMD exe

        if not self.steamcmd_check():
            log("SteamCMD Not Found And We Were Unable To Download It")
            sys.exit(0)
            
        self.multithread = multithread
        self.multithread_extraction = multithread_extraction
        self.modname = modname
        self.installed_Mods = []  # List to hold installed Mods
        self.map_names = []  # Stores map names from mod.info
        self.meta_data = OrderedDict([])  # Stores key value from modmeta.info
        self.preserve = preserve
        self.download_dir = os.path.join(self.working_dir,'.temp_ark_mod_downloader')
        self.temp_mod_path = os.path.join(self.download_dir, r"steamapps", r"workshop", r"content", r"346110")
        self.temp_steamcmd_dir = os.path.join(working_dir,temp_steamcmd_dir_name)
        
        if not self.prep_steamcmd():
            return 
            log('error prepping steam. if you are on linux then this is not supposed to happen so report it(:')

        if mod_update:
            log("[+] mod Update Is Selected.  Updating Your Existing Mods")
            return self.update_Mods()

        # If any issues happen in download and extract chain this returns false
        
        if modids:
            successfully_installed_Mods = []
            failed_to_install_Mods = []
            threads =[]
            def download_logic(mod):
                log("\n\n\n\n\n[+] downloading mod " + mod)
                download_dir = self.make_download_dir(mod)
                if self.download_mod(mod,download_dir):
                    successfully_installed_Mods.append(mod)
                else:
                    failed_to_install_Mods.append(mod)
                    log("[x] Error downloading mod " + mod)
                    

            for mod in modids:

            
                if self.multithread:
                    t = threading.Thread(target=download_logic, args=(mod,))
                    t.start()
                    threads.append(t)
                else:
                    download_logic(mod)
                
                for t in threads:
                    t.join()

                for succ_mod in successfully_installed_Mods:
                    log(f'[+] successfully downloaded mod {succ_mod}')

                for succ_mod in failed_to_install_Mods:
                    log(f'[x] Failed to download mod {succ_mod}')
    
    def clean_up():
        return
    
    def make_download_dir(self,modid):## it will add modid to the end of the temp ark mod downloader dir name
        return os.path.join(self.working_dir,f'.temp_ark_mod_downloader_{modid}')

    def make_temp_mod_path(self,download_dir):
        return os.path.join(download_dir, r"steamapps", r"workshop", r"content", r"346110")

    def create_mod_name_txt(self, mod_folder, modid):
        log(os.path.join(mod_folder, self.map_names[0] + " - " + modid + ".txt"),modid)
        with open(os.path.join(mod_folder, self.map_names[0] + ".txt"), "w+") as f:
            f.write(modid)
            
    def working_dir_check(self):
        log("[!] No working directory provided.  Checking Current Directory")
        log("[!] " + os.getcwd())
        if os.path.isdir(os.path.join(os.getcwd(), "ShooterGame","Content")):
            log("[+] Current Directory Has Ark Server.  Using The Current Directory")
            self.working_dir = os.getcwd()
        else:
            log("[x] Current Directory Does Not Contain An ARK Server. Aborting")
            sys.exit(0)

    def steamcmd_check(self):#it checks for the file called "steamcmd". create a shortcut on windows or a sym link in linux to steamcmd in the working dir
        """
        If SteamCMD path is provided verify that exe exists.
        If no path provided check TCAdmin path working dir.  If not located try to download SteamCMD.
        :return: Bool
        """
        names = ['steamcmd','steamcmd.exe','steamCMD','steamCMD.exe','steamcmd.lnk','steamCMD.lnk','steamcmd.sh','steamCMD.sh']
        def check_file(dir):
            if not os.path.isdir(dir):
                log('[x] the directory where steamcmd is supposed to be located does not exists')
                return ''
            for name in names:
                if os.path.isfile(os.path.join(dir, name)):
                    return os.path.join(dir,name)
            return ''
                
        if self.steamcmd:
            log("[+] Checking Provided Path For steamcmd")
            steamcmd = check_file(self.steamcmd)
            if os.path.isfile(steamcmd):
                self.steamcmd = steamcmd
                log("[+] steamcmd Found At Provided Path")
                return True
            else:
                log('[x] did not find steamcmd at steamcmd directory path')

        # Check working directory
        log('[+] checking working directory for steamcmd')
        steamcmd = check_file(self.working_dir)
        if os.path.isfile(steamcmd):
            log("[+] Located steamcmd")
            self.steamcmd = steamcmd
            return True

        return False

    def prep_steamcmd(self):
        if not is_windows:
            return True
        if self.steamcmd != None:
            if os.path.isfile(self.steamcmd):
                if os.path.isdir(self.temp_steamcmd_dir):
                    shutil.rmtree(self.temp_steamcmd_dir)
                    log(f'looks like it did not clean up. removed a directory that is named {self.temp_steamcmd_dir}')
                if os.path.isfile(self.temp_steamcmd_dir):
                    os.remove(self.temp_steamcmd_dir)
                    log(f'removed a file that is named {self.temp_steamcmd_dir}  because it is not supposed to exists')
                
                os.mkdir(self.temp_steamcmd_dir)
                log(f'made directory called {self.temp_steamcmd_dir}')
                
                steamcmd = self.copy_steamcmd_to_dir(self.temp_steamcmd_dir)
                log(f'copied existing steamcmd to {self.temp_steamcmd_dir}')
                
                log('running steamcmd to prep it')
                try:
                    subprocess.call([steamcmd,'+quit'],shell=False,cwd=self.temp_steamcmd_dir)
                except Exception as e:
                    log(f'error occurred while trying to run temp steamcmd {steamcmd} \n error: {e}')
                    return False
                return True
            else:
                log('steamcmd is not a file')
        else:
            log('steamcmd is not stored in a variable') 
            
        return False
                
    
    def update_Mods(self):
        self.build_list_of_Mods()
        successfully_installed_Mods = []
        failed_to_install_Mods = []

        def download_logic(mod):
            log("\n\n\n\n\n[+] Updating mod " + mod)
            download_dir = self.make_download_dir(mod)
            if self.download_mod(mod,download_dir):
                successfully_installed_Mods.append(mod)
            else:
                failed_to_install_Mods.append(mod)
                log("[x] Error Updating mod " + mod)

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
                log(f'[+] successfully updated mod {succ_mod}')

            for succ_mod in failed_to_install_Mods:
                log(f'[x] Failed to update mod {succ_mod}')
        else:
            log("[+] No Installed Mods Found.  Skipping Update")


    def build_list_of_Mods(self):
        """
        Build a list of all installed Mods by grabbing all directory names from the mod folder
        :return:
        """
        if not os.path.isdir(os.path.join(self.working_dir, "ShooterGame", "Content" , "Mods")):
            log('[!] no Mods directory found')
            return
        for curdir, dirs, files in os.walk(os.path.join(self.working_dir, "ShooterGame", "Content" , "Mods")):
            for d in dirs:
                if d == '111111111':
                    continue
                if d.isdigit():# check if it only contains digits so it doesn't try to download a map
                    self.installed_Mods.append(d)
            break
        
    def copy_steamcmd_and_files_to_dir(self,dir):
        temp_steam_exists = os.path.isdir(self.temp_steamcmd_dir)
        dir_exists = os.path.isdir(dir)
        if temp_steam_exists:
            shutil.copytree(self.temp_steamcmd_dir, dir)
            return os.path.join(dir,os.path.basename(self.steamcmd).split('/')[-1])
        else:
            sys.exit(f"Error: \n temp steam directory exists? {self.temp_steamcmd_dir}") #{temp_steam_exists} \ntarget dir exists? {dir} {dir_exists}")
    
    def copy_steamcmd_to_dir(self,dir): ## returns the path of the copied steamcmd
        steam_exists = os.path.isfile(self.steamcmd)
        dir_exists = os.path.isdir(dir)
        if steam_exists and dir_exists:
            steamcmd_new_path = os.path.join(dir,os.path.basename(self.steamcmd).split('/')[-1])
            shutil.copyfile(self.steamcmd, steamcmd_new_path)
            return steamcmd_new_path
        else:
            sys.exit(f"Error: \nsteam exists? {self.steamcmd} {steam_exists} \ntarget dir exists? {dir} {dir_exists}")
        

    def download_mod(self, modid,download_dir,preserve=False):
        preserve = preserve or self.preserve
        if os.path.isdir(download_dir) and not self.preserve:
            shutil.rmtree(download_dir)
        """
        Launch SteamCMD to download modID
        :return:
        """
        
        log("[+] Starting Download of mod " + str(modid),modid)
        args = []
        args.append(self.steamcmd)
        args.append(f"+force_install_dir '{download_dir}'") # added this to get a cleaner download.
        args.append("+login anonymous")
        args.append("+workshop_download_item")
        args.append("346110")
        args.append(modid)
        if preserve:
            args.append("validate")
        args.append("+quit")
        if os.path.isdir(self.download_dir):
            shutil.rmtree(self.download_dir)
        if os.path.isfile(self.download_dir):
            os.remove(self.download_dir)
        output = ''
        try:
            if is_windows:# check if os is windows
                steamcmd = self.copy_steamcmd_and_files_to_dir(download_dir)
                args[0] = steamcmd
                output = subprocess.check_output(args,shell=False,cwd=download_dir).decode('utf-8')
            else:
                output = subprocess.run(args, shell=False, stdout=subprocess.PIPE).stdout.decode('utf-8')
        except Exception as e:
            log('error downloading mod \n'+e)
            return False

        

        if 'Timeout downloading item' in output:
            return self.download_mod(modid,download_dir,True)
        if not 'Success. Downloaded item' in output:
            sys.exit(f'failed to download mod because of an steamcmd error check the steamcmd output to troubleshoot\n{output}')
            
        if not os.path.isdir(download_dir):# checks if steamcmd made the download_dir if not then it failed to download
            log('failed to download mod with steamcmd | aborting mod download',modid)
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

        log("[+] Extracting .z Files.",modid)
        def f(file,name,curdir):  
            src = os.path.join(curdir, file)
            dst = os.path.join(curdir, name)
            uncompressed = os.path.join(curdir, file + ".uncompressed_size")
            arkit.unpack(src, dst)
            log("[+] Extracted " + file)
            os.remove(src)
            if os.path.isfile(uncompressed):
                os.remove(uncompressed)
                
        threads =[]
        try:
            for curdir, subdirs, files in os.walk(os.path.join(self.make_temp_mod_path(download_dir), modid, "WindowsNoEditor")):
                for file in files:
                    name, ext = os.path.splitext(file)
                    if ext == ".z":
                        if self.multithread_extraction:
                            t = threading.Thread(target=f, args=(file,name,curdir,))
                            t.start()
                            threads.append(t)
                        else:
                            f(file,name,curdir)
            for t in threads:
                t.join()

        except (arkit.UnpackException, arkit.SignatureUnpackException, arkit.CorruptUnpackException) as e:
            log("[x] Unpacking .z files failed, aborting mod install",modid)
            log(e,modid)
            return False

        if self.create_mod_file(modid,download_dir):
            if self.move_mod(modid,download_dir):
                return True
            else:
                log('failed to move mod',modid)
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
            log("[+] Creating Directory: " + ark_mod_folder,modid)
            os.mkdir(ark_mod_folder)

        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

        log("[+] Moving mod Files To: " + output_dir,modid)
        shutil.copytree(source_dir, output_dir)

        if self.modname:
            log("Creating mod Name File",modid)
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

        log("[+] Writing .mod File",modid)
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

        log("[+] Collecting mod Meta Data From modmeta.info",modid)
        log("[+] Located The Following Meta Data:",modid)

        mod_meta = os.path.join(self.make_temp_mod_path(download_dir), modid, r"WindowsNoEditor", r"modmeta.info")
        if not os.path.isfile(mod_meta):
            log("[x] Failed To Locate modmeta.info. Cannot continue without it.  Aborting",modid)
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
                    log("[!] " + key + ":" + value)
                    self.meta_data[key] = value

        return True


    def parse_base_info(self, modid,download_dir):

        log("[+] Collecting mod Details From mod.info",modid)

        mod_info = os.path.join(self.make_temp_mod_path(download_dir), modid, r"WindowsNoEditor", r"mod.info")

        if not os.path.isfile(mod_info):
            log("[x] Failed to locate mod.info. Cannot Continue.  Aborting",modid)
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
    parser.add_argument("--multithread_extraction", default=None, action="store_true", dest="multithread_extraction", help="multithread the the extraction of .z files so it is faster requires more ram and cpu usage")
    args = parser.parse_args()

    if not args.modids and not args.mod_update:
        log("[x] No mod ID Provided and Update Not Selected.  Aborting")
        log("[?] Please provide a mod ID to download or use --update to update your existing Mods")
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
