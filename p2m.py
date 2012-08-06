#!/usr/bin/python2.6

#Polyphonic to Multitrack midi file Converter
#Splits all the voices of a midi file into several mono tracks and writes the result in the output midi file
#It will produce as many tracks as the maximum polyphony used at any given time in the whole file
#no limits on the voices, you can sprawl on the keyboard :)
#usage: python p2m.py -i inputfile

import os
import sys
import optparse
from midifile import *

class Voices(object):
    def __init__(self):
        #list of allocated voices/tracks, contains note numbers, 0 means a now free but previously played voice
        self.voices = list()

    def SlotOf(self, note):
        return self.voices.index(note)
    
    #looks for an empty slot, if not found allocates a new track
    #returns the slot number
    def NoteOn(self, d, note, w):
        try:
            i = self.SlotOf(0)
        except:
            self.voices.append(note)
            i = len(self.voices) - 1
            if i > 0:
                w.AddTrack()
        
        self.voices[i] = note
        return i
    
    def NoteOff(self, note):
        try:
            i = self.SlotOf(note)
            self.voices[i] = 0
            return i
        #it should never happen, but just in case it won't wreak havoc
        except:
            return -1
    
class Converter(object):
    def __init__(self):
        self.v = Voices()
    
    def Convert(self, ifname, ofname):
        r = Reader()
        w = Writer()

        #a first track always needed for a no note event occurring before a note event
        w.AddTrack()
        
        fin = file(ifname, 'rb')
        r.Read(fin)

        #Considering the limited scope of this script, tempo info tracks will be discarded
        for t in r.tracks:
            #identify a playable track
            playabletrack = False
            for _, e in t:
                if isinstance(e, NoteOnEvent):
                    playabletrack = True                 
                    break
     
            if playabletrack:     
                for d, e in t:
                    #voice specific events
                    if isinstance(e, ChannelEvent):
                        if isinstance(e, NoteOnEvent):
                            i = self.v.NoteOn(d, e.note, w)
                            #a bit unfair, but had not choice
                            w._tracks[i].AddEvent(d, e) 
                        elif isinstance(e, NoteOffEvent):
                            i = self.v.NoteOff(e.note)
                            if i >= 0:
                                w._tracks[i].AddEvent(d, e) 
                        elif isinstance(e, KeyAftertouchEvent):
                            i = self.v.SlotOf(e.note)
                            w._tracks[i].AddEvent(d, e) 
                        #any else channel event must be copied as is and propagated to the other tracks
                        else:
                            for i in 0..len(self.w._tracks) - 1:
                                w._tracks[i].AddEvent(d, e)
                    #everything else except track names will be copied to the first track
                    else:
                        if isinstance(e, TrackNameEvent):
                            trackname = e.text
                        else:
                            w._tracks[0].AddEvent(d, e) 
        
        for t in w._tracks:
            t.AddEvent(1, TrackNameEvent(trackname + '_' + str(w._tracks.index(t) + 1)))
            
        w._ppq = r.ppq
        fout = file(ofname, 'wb')    
        w.Write(fout, format=1)
        fin.close()
        fout.close()
        
        return len(w._tracks)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option(
      '-i',
      '--input_file',
      dest='input_file',
      default='Untitled.mid',
      help='input file FILE',
      metavar='FILE')

    options, _ = parser.parse_args()

    c = Converter()
    ifname = options.input_file 
    ofname = os.path.splitext(ifname)[0] + '_multi.mid'
    i = c.Convert(ifname, ofname)

    sys.stdout.write(str(i) + ' Mono Tracks Generated into ' + ofname)