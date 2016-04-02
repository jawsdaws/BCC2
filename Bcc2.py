#!/usr/bin/env python2

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

#TODO Fix Quality checking and error handling

from multiprocessing import Pool
from multiprocessing import Process
from multiprocessing import BoundedSemaphore
from multiprocessing import cpu_count
from multiprocessing import Queue
import argparse
import os
import subprocess
import random

Null = open(os.devnull, "w")


class Song( object ):

    def __init__(self):
        self.HasArt = False
        
        self.Album = " "
        self.Title = " "
        self.Artist = " "
        self.DiscNumber = " "
        self.TrackTitle = " "
        self.Art = " "
        self.TrackNumber = " "
        self.TrackTotal = " "
        self.Genre = " "
        self.Date = " "

        
    def Setup(self, OptionList):
        self.RandomFilename = "BA" + "".join(random.choice("QWERTYUIOPLKJHGFDSAZXCVBNMqwertyuioplkjhgfdfsazxcvbnm123456789") for i in xrange(6))
        self.RandomFilename = OptionList[5] + "/" + self.RandomFilename + ".wav"
        
    def sanitize(self, inString):
        unusable = ['/', '<', '>', ':', '"', '|', '?', '*']
        for i in unusable:
            inString = inString.replace(i, '-')
        return inString

    def setInputFile(self, infile):
        self.InputFile = infile

    def setOutputFile(self, OptionList):
        if OptionList[1] == 'wav':
            self.OutputFile = OptionList[2] + "/" + self.sanitize(self.InputFile.split("/")[-1]) + "." + OptionList[0]
        elif self.DiscNumber != "":
            self.OutputFile = OptionList[2] + "/" + self.sanitize(self.Artist) + "/" + self.sanitize(self.Album) + "/" + "CD " + self.DiscNumber + "/" + self.TrackNumber + " - " + self.sanitize(self.Title) + "." + OptionList[0]
        else:
            self.OutputFile = OptionList[2] + "/" + self.sanitize(self.Artist) + "/" + self.sanitize(self.Album) + "/" + self.TrackNumber + " - " + self.sanitize(self.Title) + "." + OptionList[0]

    #Write the output directory to disc
    def MkDir(self, OptionList):
        #Use try/pass here because threads can colide and cause an exception.
        try :
            if OptionList[1] == 'wav':
                os.makedirs(OptionList[2])
            elif self.DiscNumber != "":
                os.makedirs(OptionList[2] + "/" + self.sanitize(self.Artist) + "/" + self.sanitize(self.Album) + "/" + "CD " + self.DiscNumber)
            else:
                os.makedirs(OptionList[2] + "/" + self.sanitize(self.Artist) + "/" + self.sanitize(self.Album))
        except :
            pass

    def Decode(self, OptionList):
        if OptionList[1] == "flac":
            DecFlac(self.InputFile, self.RandomFilename)
            ReadFlacTag(self, self.InputFile)
        elif OptionList[1] == "wv":
            DecWv(self.InputFile, self.RandomFilename)
            ReadApeTag(self, self.InputFile)
        elif OptionList[1] == "wav":
            DecWav(self.InputFile, self.RandomFilename)
    
    def Encode(self, OptionList):
        if OptionList[0] == "mp3":
            EncMp3(self, OptionList[3])
            TagMp3(self)
        elif OptionList[0] == "ogg":
            EncOgg(self, OptionList[3])
            TagOgg(self)
        elif OptionList[0] == "m4a":
            EncAac(self, OptionList[3])
            TagAac(self)
        elif OptionList[0] == "wv":
            EncWv(self, OptionList[3])
            TagWv(self)
        elif OptionList[0] == "mpc":
            EncMpc(self, OptionList[3])
            TagMpc(self)
            

    def ReadArt(self):
        for root, dirs, files in os.walk(os.path.dirname(self.InputFile)):
            for file in files:
                ends = os.path.splitext(file)
                if (ends[1] == '.jpg') or (ends[1] == '.jpeg')  or (ends[1] == '.png'):
                    self.Art = open(os.path.dirname(self.InputFile) + "/" + file, "rb").read()

    def CleanUp(self):
        if os.path.exists(self.RandomFilename):
            os.remove(self.RandomFilename)
        if os.path.exists(self.RandomFilename + ".aac"):
            os.remove(self.RandomFilename + ".aac")


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
    def setGenre(self, genre):
        self.Genre = genre
    def setDiscNumber(self, discnum):
        self.DiscNumber = discnum
    def setDate(self, date):
        self.Date = date


def Initlize():
    try:
        import mutagen.flac
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

    OptionList = [args.OutputCodec, args.InputCodec, args.OutputDir, args.OutputQuality, args.InputDir, args.TempDir]
    OptionList[0] = OptionList[0].lower()
    OptionList[1] = OptionList[1].lower()

    if args.TempDir == None:
        OptionList[5] = "/tmp"
    else:
        OptionList[5] = args.TempDir
    if not os.path.exists(OptionList[5]):
        print ("Temp directory does not exist.")
        raise SystemExit
    if os.access(OptionList[5], os.W_OK) == False:
        print ("Temp directory is not writeable.  Please check your permissons")
        raise SystemExit

    return OptionList

#Check if we can contiune with the codecs selected
def CodecCheck(OptionList):
    
    #Lists for supported codecs
    SupportedOut = ["mp3", "ogg", "mpc", "m4a", "wv", "flac"]
    SupportedIn = ["wv", "flac", "ape", "wav"]
    
    if OptionList[0] not in SupportedOut:
        print ("Codec not Supported as Output")
        raise SystemExit
    if OptionList[1] not in SupportedIn:
        print ("Codec not Supported as Input")
        raise SystemExit

#Check if the needed encoder commands are installed
def EncoderBinaryCheck(Option):
    
    Null = open(os.devnull, "w")
    
    EncodeBinaryDic = {"mp3" : "lame", "ogg" : "oggenc", "mpc" : "mpcenc", "m4a" : "aac-enc", "wv" : "wavpack", "flac" : "flac"}
    
    try:
        subprocess.call([EncodeBinaryDic.get(Option)], stdout=Null, stderr=Null)
    except:
        print("%s encoder (%s) is not installed" %(Option, EncodeBinaryDic.get(Option))) 
        raise SystemExit
    
    
#Check if the needed decoder commands are installed
def DecoderBinaryCheck(Option):

    Null = open(os.devnull, "w")
    
    if Option == "wav":
        return
    DecodeBinaryDic = {"wv" : "wvunpack", "flac" : "flac", "ape" : "mplayer"}
    
    try:
        subprocess.call([DecodeBinaryDic.get(Option)], stdout=Null, stderr=Null)
    except:
        print("%s decoder (%s) is not installed" %(Option, DecodeBinaryDic.get(Option))) 
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
    
#Tag Reader************************************************************************************************
def ReadFlacTag(Song, fullpathfile):
    from mutagen.flac import FLAC
    MetaData = FLAC(fullpathfile)
    try:
        Song.Art = MetaData.pictures[0].data
    except:
        Song.ReadArt()
           
    for t in MetaData.items():
        if t[0] == "tracknumber":
            Song.setTrackNumber(t[1][0])
        elif t[0] == "tracktotal":
            Song.setTrackTotal(t[1][0])
        elif t[0] == "genre":
            Song.setGenre(t[1][0])
        elif t[0] == "title":
            Song.setTitle(t[1][0])
        elif t[0] == "discnumber":
            Song.setDiscNumber(t[1][0])
        elif t[0] == "album":
            Song.setAlbum(t[1][0])
        elif t[0] == "date":
            Song.setDate(t[1][0])
        elif t[0] == "artist":
            Song.setArtist(t[1][0])
            
def ReadApeTag(Song, fullpathfile):
    import mutagen.apev2
    MetaData = mutagen.apev2.Open(fullpathfile)
    try:
        Song.Art = MetaData.pictures[0].data
    except:
        Song.ReadArt()
        
    if '/' in MetaData['track'][0]:
        TrackList = MetaData['track'][0].split('/')
        Song.setTrackNumber(TrackList[0])
        Song.setTrackTotal(TrackList[1])
    else:
        Song.setTrackNumber(MetaData['track'][0])
    for t in MetaData.items():
        if t[0].lower() == "genre":
            Song.setGenre(t[1][0])
        elif t[0].lower() == "title":
            Song.setTitle(t[1][0])
        elif t[0].lower() == "part":
            Song.setDiscNumber(t[1][0])
        elif t[0].lower() == "album":
            Song.setAlbum(t[1][0])
        elif t[0].lower() == "year":
            Song.setDate(t[1][0])
        elif t[0].lower() == "artist":
            Song.setArtist(t[1][0])

#Decoder******************************************************************************************************
def DecFlac(fullpathfile, TempFilename):
    subprocess.call( ["flac", "-f", "-d", fullpathfile, "-o", TempFilename], stdout=Null, stderr=Null )

def DecWv(fullpathfile, TempFilename):
    subprocess.call( ["wvunpack", "-y", fullpathfile, "-o", TempFilename], stdout=Null, stderr=Null )
    
def DecWav(fullpathfile, TempFilename):
    from shutil import copy
    copy(fullpathfile, TempFilename)

#Encoder******************************************************************************************************
def EncMp3(Song, OutQua):
    subprocess.call( ["lame", "-t", "-%s" %(OutQua), Song.RandomFilename, "%s" %(Song.OutputFile) ], stdout=Null, stderr=Null )

def EncAac(Song, OutQua):
    subprocess.call( ["fdkaac", "-b", OutQua, Song.RandomFilename, "-o", "%s" %(Song.OutputFile) ],  stdout=Null, stderr=Null )
    #subprocess.call( ["aac-enc", "-v", OutQua, "-t", "2", "-s", "0", "-a", "1", Song.RandomFilename, Song.RandomFilename + ".aac"], stdout=Null, stderr=Null )
    #subprocess.call( ["MP4Box", "-add", Song.RandomFilename + ".aac", "-new", Song.OutputFile], stdout=Null, stderr=Null )

def EncWv(Song, OutQua):
    subprocess.call( ["wavpack", "-y", "-%s" %(OutQua), "-i", Song.RandomFilename, "-o", Song.OutputFile], stdout=Null, stderr=Null )

def EncOgg(Song, OutQua):
    subprocess.call( ["oggenc", "-q", OutQua, Song.RandomFilename, "-o", Song.OutputFile], stdout=Null, stderr=Null )
    
def EncMpc(Song, OutQua):
    subprocess.call( ["mpcenc", "--overwrite", "--quality", OutQua, Song.RandomFilename, Song.OutputFile], stdout=Null, stderr=Null )

#Tagger******************************************************************************************************
def TagOgg(Song):
    from mutagen.oggvorbis import OggVorbis
    MetaData = OggVorbis(Song.OutputFile)
    MetaData['TITLE'] = Song.Title
    MetaData['ARTIST'] = Song.Artist
    MetaData['ALBUM'] = Song.Album
    MetaData['TRACKNUMBER'] = Song.TrackNumber
    MetaData['TRACKTOTAL'] = Song.TrackTotal
    MetaData['GENRE'] = Song.Genre
    MetaData['DATE'] = Song.Date
    MetaData['DISCNUMBER'] = Song.DiscNumber
    
    if Song.Art != '':
        from mutagen.flac import Picture
        import base64
        
        picture = Picture()
        picture.data = Song.Art
        
        picture_data = picture.write()
        encoded_data = base64.b64encode(picture_data)
        vcomment_value = encoded_data.decode("ascii")
        MetaData["metadata_block_picture"] = [vcomment_value]
    
    MetaData.save()
    
def TagMpc(Song):
    #ApeTags do not support pictures
    from mutagen.musepack import Musepack
    MetaData = Musepack(Song.OutputFile)
    MetaData['Title'] = Song.Title
    MetaData['Artist'] = Song.Artist
    MetaData['Album'] = Song.Album
    MetaData['Track'] = Song.TrackNumber + "/" + Song.TrackTotal
    MetaData['Genre'] = Song.Genre
    MetaData['Year'] = Song.Date
    MetaData['Part'] = Song.DiscNumber
    MetaData.save()
    
def TagWv(Song):
    #ApeTags do not support pictures
    from mutagen.wavpack import WavPack
    MetaData = WavPack(Song.OutputFile)
    MetaData['Title'] = Song.Title
    MetaData['Artist'] = Song.Artist
    MetaData['Album'] = Song.Album
    MetaData['Track'] = Song.TrackNumber + "/" + Song.TrackTotal
    MetaData['Genre'] = Song.Genre
    MetaData['Year'] = Song.Date
    MetaData['Part'] = Song.DiscNumber
    MetaData.save()
    
def TagAac(Song):
    from mutagen.mp4 import MP4, MP4Cover
    MetaData = MP4(Song.OutputFile)
    MetaData['\xa9ART'] = Song.Artist
    MetaData['\xa9alb'] = Song.Album
    MetaData['\xa9gen'] = Song.Genre
    MetaData['\xa9day'] = Song.Date
    MetaData['\xa9nam'] = Song.Title
    
    #This is to error check for files that have no Total set
    if Song.TrackNumber != '' and Song.TrackTotal != '':
        num = int(Song.TrackNumber)
        tot = int(Song.TrackTotal)
        MetaData['trkn'] = [ (num, tot) ]
    elif Song.TrackNumber != '' and Song.TrackTotal == '':
        num = int(Song.TrackNumber)
        MetaData['trkn'] = [(num, 0)]
    
    if Song.DiscNumber != '':
        dnum = int(Song.DiscNumber)
        MetaData['disk'] = [ (dnum, 0) ]
    if Song.Art != '':
        MetaData['covr'] = [MP4Cover(Song.Art, MP4Cover.FORMAT_JPEG)]
    MetaData.save()
    
def TagMp3(Song):
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, APIC
    
    MetaData = mutagen.File(Song.OutputFile, easy=True)
    MetaData.add_tags()
    MetaData['title'] = Song.Title
    MetaData['artist'] = Song.Artist
    MetaData['album'] = Song.Album
    MetaData['tracknumber'] = Song.TrackNumber + "/" + Song.TrackTotal
    MetaData['genre'] = Song.Genre
    MetaData['date'] = Song.Date
    MetaData['discnumber'] = Song.DiscNumber
    MetaData.save(Song.OutputFile, v1=2)
    
    MetaData2 = ID3(Song.OutputFile)
    #MetaData2.add(APIC(encoding=3, mime=Song.Art, type=3, desc=u'Cover',data=open(Song.Art).read()))
    MetaData2.add(APIC(encoding=3, type=3, desc=u'Cover',data=Song.Art))
    MetaData2.save()

#Main*********************************************************************************************************
def main():
    
    def Encoder (song, OptionList, sem):
        sem.acquire()
        song.Setup(OptionList)
        song.Decode(OptionList)
        print("Decode " + song.InputFile)
        song.setOutputFile(OptionList)
        song.MkDir(OptionList)
        song.Encode(OptionList)
        print("Encoding " + song.OutputFile)
        song.CleanUp()
        sem.release()
    
    CPU = cpu_count()
    sem = BoundedSemaphore(CPU)
    
    Initlize()
    
    OptionList = ParseCommandLine()
    CodecCheck(OptionList)
    EncoderBinaryCheck(OptionList[0])
    DecoderBinaryCheck(OptionList[1])
    InputDirectoryCheck(OptionList)
    SongList = BuildSongList(OptionList)
    
    for song in SongList:
        sem.acquire()
        p = Process(target=Encoder, args=(song, OptionList, sem))
        p.start()
        sem.release()
    
    

if __name__ == "__main__":
    main()
