# What is this
My (kangalioo) sync tool helps you sync charts to songs. It aims to be especially useful for songs with freaky BPMs that are tricky to model manually, such as live music. The core idea behind the tool is not to _guess_ the BPM and offset of an audio file (that's difficult and unreliable). Instead, **it aims to precisely calculate BPM changes using explicit labels on that audio file.**

Therefore the catch is that you won't be able to use this for songs without clear beat boundaries (i.e. drum hits). That means that this is primarily meant for EDM; things like Acapella or Orchestra music which have vague beat - not so much.

This tool uses the Audacity label functionality. If you haven't installed Audacity, you can install it for free as it's open-source. Load your audio file into Audacity and go wild creating labels using the Ctrl+B shortcut (you'll learn about the types of markers below). When you're done, export the labels via `File -> Export -> Export Labels`. Drag the resulting .txt file onto my tool's exe file ([download](https://github.com/kangalioo/synctool/releases)), and it will create a `sync-values-output.txt` file looking similar to this:
```
#BPMS:0.000000=171.288809
,222.000000=171.177361
,241.989583=137.000000
,442.145833=171.288678
,693.911458=137.000000
;
#OFFSET:-1.102368;
```
Now, go into the .sm file of your chart, delete the #OFFSET line and also all the lines from #BPMS until the next line starting with a #. Then paste in the content of `sync-values-output.txt`. With this you've successfully replaced the sync values. Reload your editor to see the changes.

Now as to how the labeling actually works.

# Types of markers
In Audacity there are point labels and region labels (I'll call them markers from now on). Markers in Audacity contain a text, which can be blank too. My tool interprets the markers in different ways depending on their type and text.

All markers except the BPM-change pinpointing marker need to be exactly aligned to the beat. Be careful that you have accurate alignment, or the resulting BPM values will be slightly off. At the bottom of this document I will explain how to align your markers to kick drum hits perfectly.

## BPM determination marker
This is the most useful type of marker. It spans a certain number of beats and contains the exact number of beats in the marker text.
![BPM determination marker example](https://imgur.com/9Nso91N.png)
Just one of these is enough to calculate the offset and BPM for a song, given that it has a constant BPM. Where you place this marker is irrelevant to the syncing. Just find a spot where it's easy for you to discern the drum hits, and make this marker as long as possible for the most precise BPM measurement.

## Boundary marker
A blank point marker will instruct the program to calculate a BPM change at that point. If it follows a BPM determination marker, it will also adjust BPM "drifting" issues (you should know what that is if you ever needed to determine a weird BPM like 154.687 or something like that). The program will adjust the previous BPM to align perfectly with the boundary marker.

Example for this behavior:
![](https://imgur.com/ukJJV9u.png)The BPM determination marker (left) is 34 beats long, which makes it pretty precise already. At the right I've inserted a boundary marker, which will slightly adjust the BPM from the determination marker on the left, so that it will be _perfectly_ on-sync with the boundary marker.

A boundary marker can be used for another purpose:
![Example of a boundary marker being used to model a BPM slope](https://imgur.com/lewjjsR.png)
A boundary marker can also be used to model continually changing BPMs, such as in live music or in BPM slopes (see example above). In such situations, place boundary markers at every beat, or every second beat or so. For each boundary marker there will be a BPM calculated, so that all the beats align well even though their BPM is changing all the time.

Be aware that you need to have a dummy marker at the end of such a section, as in the picture above.

## BPM-change pinpointing
Some songs change their BPM mid-song. The program provides a way to pinpoint the exact time where those BPM changes occur. To do that, find the song region in which the BPM change must be happening somewhere. Create a blank region marker there. The program will scan that region to find the BPM change's exact position.
![](https://imgur.com/pGBwW4Q.png)In this example I've used BPM determination markers to find the BPMs of the first and second part. In the middle you see a blank region marker - this instructs the program to pinpoint where the BPM step-up happens.

## BPM markers
In cases where you already know the exact BPM of a song, simply create a beat-aligned marker somewhere with the BPM as the text.
![](https://imgur.com/O5pyttb.png)

# How to align
For best results you need to align your markers perfectly to beat boundaries. Many EDM songs conveniently have kick drum hits placed on every beat - let's use those :)

The secret to pinpointing kick drum hits is zooming in. So let's do that, step for step.
**Zoom level 1**
![](https://imgur.com/LkMcXpf.png)This a song in its entire beauty. Starting at approximately 1:01 the drop starts where the kick drum is most prominent.
**Zoom level 2**
![](https://imgur.com/hDZUylB.png)This is the first 20 seconds of the drop. You can already make out the kick drums. Let's zoom in on one of the kick drums.
**Zoom level 3**
![](https://imgur.com/fwpRXQx.png)One singular kick drum. It's characterized by a sharp spike in volume (1) and then a sound wave with rapidly decreasing frequency (2). We're interested in the sharp spike because that's where we will place our markers.
**Zoom level 4**
![](https://imgur.com/wuB8nqs.png)This is the initial volume spike of the kick drum, really far zoomed in. It's easy to tell where the kick drum begins in this song - be prepared to hit more difficult cases in other songs. It's almost always possible to discern the kick drum hit though.
**Zoom level 5**
![](https://imgur.com/MGzIvse.png)
Now we've arrived at the microscopic level where we can see the individual data points the audio file is made out of. In the picture you can see the cursor; that's where I would place my marker.

Don't feel pressured to zoom in as far as I like to do. As long as you're not a perfectionist like me it, it's totally sufficient to stop at zoom level 4, or maybe 3 if you're careful.
