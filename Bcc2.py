#!/usr/bin/env python3

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import subprocess
import random


class Song( object ):

    def __init__(self):
        self.HasArt = False
        self.RandomFilename = "BA" + "".join(random.choice("QWERTYUIOPLKJHGFDSAZXCVBNMqwertyuioplkjhgfdfsazxcvbnm123456789") for i in xrange(6))
        self.Album = ""
        self.Title = ""
        self.Artist = ""
        
    def sanitize(self, inString):
        unusable = ['/', '<', '>', ':', '"', '|', '?', '*']
        for i in unusable:
            inString = inString.replace(i, '-')
        return inString

    def setAlbum(self, album):
        self.Album = album
    def setTitle(self, title):
        self.Title = title
    def setArtist(self, artist):
        self.Artist = artist
    def setTrackNumber(self, tracknumber):
        self.TrackNumber = tracknumber
    def setTrackTotal(self, tracktotal):
        self.TrackTotal = tracktotal
    def setInputFile(self, infile):
        self.InputFile = infile
    def setOutputFilePath(self, outfile):
        self.OutputFile = self.sanitize(outfile)

def Initlize():
    try:
        import mutagen.flac
        import mutagen.apev2
    except:
        print("python-mutagen could not be imported. Is it installed?")
        raise SystemExit

def ParseCommandLine():
    parser = argparse.ArgumentParser(description='Audio file converter')
    parser.add_argument("-od", action="store", dest="OutputDir", help="Output destination directory", required=True)
    parser.add_argument("-ic", action="store", dest="InputCodec", help="Input codec \"Required\"", required=True)
    parser.add_argument("-oc", action="store", dest="OutputCodec", help="Output codec \"Required\"", required=True)
    parser.add_argument("-oq", action="store", dest="OutputQuality", help="Output quality \"Required\"", required=True)
    parser.add_argument("-id", action="store", dest="InputDir", help="Input directory", required=True)
    parser.add_argument("-t", action="store", dest="TempDir", help="Working directory : /tmp is the default")
    parser.add_argument("-S", action="store_const", dest="Silent", const="True", default="False", help="A nice clean screen, don't ya know")

    args = parser.parse_args()

#Fix ME This will not work because the TempDir goes out of scope
#    #Set the temp directory
#    if args.TempDir == None:
#3        TempDir = "/tmp"
#\    else:
#        TempDir = args.TempDir
#    if not os.path.exists(TempDir):
#3        print ("Temp directory does not exist.")
#        raise SystemExit
#    if os.access(TempDir, os.W_OK) == False:
#        print ("Temp directory is not writeable.  Please check your permissons")
#        raise SystemExit
    
    OptionList = [args.OutputCodec, args.InputCodec, args.OutputDir, args.OutputQuality, args.InputDir]
    OptionList[0] = OptionList[0].lower()
    OptionList[1] = OptionList[1].lower()
    return OptionList

#Check if we can contiune with the codecs selected
def CodecCheck(OptionList):
    
    #Lists for supported codecs
    SupportedOut = ["mp3", "ogg", "mpc", "aac", "wv", "flac"]
    SupportedIn = ["wv", "flac", "ape"]
    
    if OptionList[0] not in SupportedOut:
        print ("Codec not Supported as Output")
        raise SystemExit
    if OptionList[1] not in SupportedIn:
        print ("Codec not Supported as Input")
        raise SystemExit

#Check if the needed binary commands are installed
def BinaryCheck(OptionList):

    Null = open(os.devnull, "w")
    
    #Binary keys
    DecodeBinaryDic = {"wv" : "wvunpack", "flac" : "flac", "ape" : "mplayer"}
    EncodeBinaryDic = {"mp3" : "lame", "ogg" : "oggenc", "mpc" : "mpcenc", "aac" : "neroAacEnc", "wv" : "wavpack", "flac" : "flac"}
    TaggerBinaryDic = {"mp3" : "lame", "mpc" : "mpcenc", "wv" : "wavpack", "ogg" : "vorbiscomment", "aac" : "neroAacTag", "flac" : "metaflac"}
    
    for binary in (DecodeBinaryDic, EncodeBinaryDic, TaggerBinaryDic):
        try:
            subprocess.call([binary.get(OptionList[1])], stdout=Null, stderr=Null)
        except:
            print("%s decoder (%s) is not installed" %(OptionList[1], DecodeBinaryDic.get(OptionList[1]))) 
            raise SystemExit

#Check if input directory exists
def InputDirectoryCheck(OptionList):

    if not os.path.exists(OptionList[4]):
        print ("Input directory does not exist")
        raise SystemExit

def BuildSongList(OptionList):
    
    SongList = []
    
    for root, dirs, files in os.walk(OptionList[4]):
        for file in files:       
            if file.endswith('.%s' %(OptionList[1])):
                song = Song()
                song.setInputFile(os.path.join(root, file))
                SongList.append(song)
    
    return SongList
    
def main():
    Initlize()
    
    OptionList = ParseCommandLine()
    CodecCheck(OptionList)
    BinaryCheck(OptionList)
    InputDirectoryCheck(OptionList)
    SongList = BuildSongList(OptionList)
    
    for i in SongList:
        print (i.RandomFilename)
    
    
if __name__ == "__main__":
    main()
