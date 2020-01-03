import math

def pinpoint_bpm_change(time_a, bpm_a, time_b, bpm_b, nearest_bet, alignment_b):
    from math import ceil, log10

    length = time_b - time_a
    beat_len_a = 60 / bpm_a
    beat_len_b = 60 / bpm_b
    nearest_bet -= time_a

    def final_beat(change_time):
        beats_a = change_time / beat_len_a
        beats_b = (length - change_time) / beat_len_b
        return beats_a + beats_b

    target_final_beat = round(final_beat(nearest_bet) / alignment_b) * alignment_b

    def find_relative_change_time_fast():
        # Derived through WolframAlpha
        return beat_len_a * (length - beat_len_b * target_final_beat) / (beat_len_a - beat_len_b)

    def find_relative_change_time_slow(target_res = 10e-8):
        slope = 1 if final_beat(0) < final_beat(length) else -1
        
        res = length / 4 * 4
        change_time = nearest_bet
        while res > target_res:
            if final_beat(change_time) < target_final_beat:
                change_time += slope * res
            else:
                change_time -= slope * res
            res /= 2
        res *= 2

        change_time = round(change_time, -ceil(log10(res)))
        return change_time
    
    return time_a + find_relative_change_time_fast()
    # ~ return time_a + find_relative_change_time_slow()

def lcm(a, b):
    return abs(a*b) // math.gcd(a, b)

# Snaps to whole number if it's near, leave as is if it isn't. E.g:
# 150.00037 -> 150
# 150.50037 -> 150.50037
def snap_bpm(bpm):
    snapped = round(bpm)
    if abs(bpm - snapped) < 0.1:
        return snapped
    else:
        return bpm

class Marker:
    # Possible types: "known", "point", "region", "change", "dummy", "beats"
    def __init__(self, type_, time, data, alignment):
        self.type_ = type_
        self.time = time
        self.data = data
        self.alignment = alignment;

class BpmMap:
    def __init__(self):
        self.markers = []
    
    def insert(self, type_, time, data, alignment):
        from bisect import bisect
        
        index = bisect([m.time for m in self.markers], time)
        self.markers.insert(index, Marker(type_, time, data, alignment))
    
    def next(self, start_index, matcher, reverse=False):
        time = self.markers[start_index].time
        
        if reverse:
            index_iter = reversed(range(start_index))
        else:
            index_iter = range(start_index + 1, len(self.markers))
        for i in index_iter:
            marker = self.markers[i]
            
            if reverse:
                if marker.time >= time: continue
            else:
                if marker.time <= time: continue
            
            if (matcher)(marker):
                return marker
            elif marker.type_ == "dummy":
                pass # Ignore dummy markers
            else:
                print(f"Warning: encountered unexpected '{marker.type_}' marker")
        
        raise Exception("No matching marker found")
    
    def next_point_marker(self, start_index):
        return self.next(start_index, lambda m: m.type_ != "region")
    
    def next_known(self, start_index):
        return self.next(start_index, lambda m: m.type_ == "known")
    
    def prev_known(self, start_index):
        return self.next(start_index, lambda m: m.type_ in ["known", "change"], reverse=True)

def read_markers(path):
    markers = BpmMap()
    
    for line in open(path).readlines():
        start, end, string = line[:-1].split("\t")
        
        start = float(start)
        end = float(end)
        
        args = []
        if ":" in string:
            string, args = string.split(":")
            args = args.split(",")
        try:
            value = float(string)
        except ValueError:
            value = None
        
        bpm = value # BPM variable may be garbage
        if bpm:
            beat_offset = 0
            for arg in args:
                if arg[0] == "-": beat_offset -= float(arg[1:])
                if arg[0] == "+": beat_offset += float(arg[1:])
            offset = beat_offset * 60 / bpm
            start += offset
            end += offset
        alignment = 1
        for arg in args:
            if arg[0] == "/":
                alignment = int(arg[1:])
                break
        
        if start == end: # Point marker
            time = start
            if bpm:
                markers.insert("known", time, bpm, alignment)
            elif string == "dummy":
                markers.insert("dummy", time, None, alignment)
            else:
                markers.insert("point", time, None, alignment)
        else: # Region marker
            if bpm:
                markers.insert("beats", start, (end - start, value), alignment)
            else:
                markers.insert("region", start, end - start, alignment)
    return markers

def fill_in_markers(markers):
    for marker in markers.markers:
        if marker.type_ == "beats":
            length, num_beats = marker.data
            bpm = 60 / (length / num_beats)
            bpm = snap_bpm(bpm)
            
            print(f"Calculated bpm at {marker.time:.6f}s: {bpm:.6f} BPM")
            
            marker.type_ = "known"
            marker.data = bpm
    
    for marker_i, marker in enumerate(markers.markers):
        if marker.type_ == "region":
            guess = marker.time + marker.data / 2
            a = markers.prev_known(marker_i)
            b = markers.next_known(marker_i)
            bpm_a, bpm_b = a.data, b.data
            
            print("Calling bpm_change fn with", a.time, bpm_a, b.time, bpm_b, guess)
            time = pinpoint_bpm_change(a.time, bpm_a, b.time, bpm_b, guess, b.alignment)
            print(f"Pinpointed bpm change from {bpm_a:.6f} BPM to {bpm_b:.6f} BPM at {time:.6f}s")
            
            marker.type_ = "change"
            marker.time = time
            marker.data = bpm_b
            # TODO: remove b marker
        elif marker.type_ == "point":
            curr = marker
            nxt = markers.next_point_marker(marker_i)
            prev = markers.prev_known(marker_i)
            
            alignment = lcm(curr.alignment, prev.alignment)
            
            # Adjust previous-to-current interval
            if prev.type_ != "change":
                # If previous marker type was change it originated from
                # this branch of code, which has these 'adjustments'
                # already incorporated. In fact, removing this wrapping
                # if-statement wouldn't change the output whatsoever
                length = curr.time - prev.time
                num_beats = round(length / (60 / prev.data))
                prev_bpm = 60 / (length / num_beats)
                print(f"Adjusted prev bpm from {prev.data:.6f} to {prev_bpm:.6f}")
                prev.data = prev_bpm
            
            # Determine current-to-next interval
            length = nxt.time - curr.time
            num_beats = length / (60 / prev_bpm)
            num_beats = round(num_beats / alignment) * alignment
            bpm = 60 / (length / num_beats)
            print(f"Determined bpm at point {curr.time:.6f}s as {bpm:.6f} BPM")
            marker.type_ = "change"
            marker.data = bpm

def print_info(labels_path, write_into_file):
    markers = read_markers(labels_path)
    fill_in_markers(markers)
    line = "#BPMS:"

    # IMPORTANT: First 'known' or 'change' marker must lie on a bar boundary!
    total_beats = 0
    for i, marker in enumerate(markers.markers):
        if marker.type_ not in ["known", "change"]: continue
        time, bpm = marker.time, marker.data
        if i == 0:
            offset = time % (60 / bpm * 4)
            time = offset
        else:
            if bpm == prevbpm: continue
            unsnapped_beats = (time - prevtime) / (60 / prevbpm)
            beats = round(unsnapped_beats * 192) / 192
            print(f"Nerfed time from {time} to ", end="")
            time = prevtime + (time - prevtime) * beats / unsnapped_beats
            print(f"{time}")
            total_beats += beats
        
        line += f"{total_beats:.6f}={bpm:.6f}\n,"
        
        prevtime = time
        prevbpm = bpm

    line = line[:-1] + ";"

    print()
    print("Done!")
    print()
    if write_into_file:
        with open("sync-values-output.txt", "w") as f:
            f.write(line)
            f.write(f"\n#OFFSET:-{offset:.6f};")
        print("Successfully wrote sync values into sync-values-output.txt")
        print("Copy those into your .sm file and reload your editor to see the changes")
    else:   
        print(line)
        print()

def main():
    import sys, logging
    logger = logging.getLogger()
    
    try:
        if len(sys.argv) == 1:
            print_info("/home/kangalioo/Label Track.txt", False)
        elif len(sys.argv) == 2:
            print_info(sys.argv[1], True)
        else:
            print("Please supply maximum one command line argument")
    except:
        logger.exception("AN ERROR OCCURED report this to me (kangalioo) please")
    
    print()
    input("[Press enter to quit]")

main()
