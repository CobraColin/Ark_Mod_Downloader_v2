# Ark_Mod_Downloader_v2
Ark_Mod_Downloader made by github user barrycarey looks to be abandoned, does not work on linux and other problems.

i have stolen code in order to make it better not to steal credits (:

orginal Ark_Mod_Downloader made by barrycarey: https://github.com/barrycarey/Ark_Mod_Downloader
credit: https://github.com/barrycarey


USAGE:

--workingdir - (Optional) - This is the home directory of your ARK server

--modids - The IDs of the mod you wish to download. Space separated list of Mod IDs to download

--steamcmd - (Optional) - The directory to the SteamCMD exe you wish to use.

--update - (Optional) - This will update all current mods installed on the server

--namefile - (Optional) - This will create a "Modname.name" file in the mod folder.

--preserve - (Optional) - this will not remove the temp directory where to mod is to be downloaded when it stops or you restart the                             program. i don't think this is needed except if the program stopped and you want to restart it
--multithreading - (Optional) - this will multi thread the download of the mods(in an update or a list of modids)

Example windows:
```py Ark_Mod_Downloader.py --workingdir 'C:\Program Files (x86)\Steam\steamapps\common\ARK' --modids 1210379301 2924894460
--steamcmd 'C:\Users\smelly gamer\Ark_Mod_Downloader_v2'```

Example linux:
```py Ark_Mod_Downloader.py --workingdir '/home/ark/server' --update --steamcmd '/home/ark/Ark_Mod_Downloader_v2'```

