import re

## POSSIBLE CONVERSION RATE: 1 PS point = 1.333 pixels
## (according to http://www.unitconversion.org/typography/postscript-points-to-pixels-x-conversion.html)



def parse_postscript(filename):
    # Some important constants we'll find/already know
    PAGE_HEIGHT = 0
    PAGE_WIDTH = 0
    STAFF_HEIGHT = 0
    first_line_start = 14.2264
    other_lines_start = 5.6906

    # Stuff we'll be returning
    all_bar_lines = []
    postscript_info = []
    page_breaks = []

    
    # Read in file
    psfile = open(filename)
    readfile = psfile.read()
    lines = re.split("\n",readfile)
    psfile.close()
    
    staff_height_found = False
    
    # Find bar lines
    temp_bar_lines = []
    page = -1
    current_line = 0
    for i in range(len(lines)):
        if "draw_round_box" in lines[i]:
            split_line = re.split("\s",lines[i])
            if split_line[0] == '0.1900':
                if not staff_height_found:
                    STAFF_HEIGHT = float(split_line[1])
                    staff_height_found = True
                split_position = re.split("\s",lines[i-1])
                pos_x = float(split_position[0])
                pos_y = float(split_position[1])
                if pos_y < 0:
                    pos_y *= -1
                    
                location = (pos_x, pos_y, current_line)
                
                # Special case for first line on first page - it starts slightly
                # indented, so have to compensate for that
                if len(temp_bar_lines) == 0 and page == 0:
                    first_bar = (first_line_start,location[1], current_line)
                    temp_bar_lines.append(first_bar)
                    temp_bar_lines.append(location)
                   
                # Case where we've just started a new line
                elif len(temp_bar_lines) == 0:
                    first_bar = (other_lines_start,location[1], current_line)
                    temp_bar_lines.append(first_bar)
                    temp_bar_lines.append(location)
                

                # We were already on a line - if this bar is on the same line, add it to
                # the list. If it's on a new line, sort the old line, add it to
                # the overall list, blank the list, and start over
                else:
                    if location[1] == temp_bar_lines[0][1]: 
                        temp_bar_lines.append(location)
                    else:
                        temp_bar_lines.sort()
                        for item in temp_bar_lines:
                            all_bar_lines.append(item)
                        temp_bar_lines = []
                        current_line += 1
                        location = (location[0],location[1],current_line)
                        first_bar = (other_lines_start,location[1],current_line)
                        temp_bar_lines.append(first_bar)
                        temp_bar_lines.append(location)

        # Grab global variables page height and width                
        elif "/page-height" in lines[i]:
            split_line = re.split("\s",lines[i])
            PAGE_HEIGHT = float(split_line[1])
        elif "/page-width" in lines[i]:
            split_line = re.split("\s",lines[i])
            PAGE_WIDTH = float(split_line[1])

        # Check if there is a page break
        elif "%%Page:" in lines[i]:
            page += 1
            temp_bar_lines.sort()
            for item in temp_bar_lines:
                all_bar_lines.append(item)
                temp_bar_lines = []
            if len(all_bar_lines) == 0:
                page_breaks.append(0)    
            else:
                page_breaks.append(len(all_bar_lines)+1)
                current_line += 1
           

    # Grab the rest of the things in temp_bar_lines
    temp_bar_lines.sort()
    for item in temp_bar_lines:
        all_bar_lines.append(item)

    # Convert from PostScript units to percentage-of-page
    converted_bar_lines,bar_line_positions = \
        convert_units(all_bar_lines,PAGE_HEIGHT,PAGE_WIDTH,STAFF_HEIGHT)
            
    #print bar_line_positions
    postscript_info.append(STAFF_HEIGHT/PAGE_HEIGHT)
    postscript_info.append(page_breaks)
    postscript_info.append(bar_line_positions)

    measures = barlines_to_measures(converted_bar_lines)
    
    return measures, postscript_info

def convert_units(all_bar_lines, PAGE_HEIGHT, PAGE_WIDTH, STAFF_HEIGHT):
    '''Does two things, which is bad. CONVENTION BE DAMNED. 1) Converts
    the units of our distance measures from PostScript points to percentage
    of the page. 2) Returns a list of where each line starts and ends,
    y-axis-wise.'''
    try:
        top_of_line = 0
        bar_line_positions = []
        temp_line_positions = []
        for i in range(len(all_bar_lines)):
            line_number = all_bar_lines[i][2]
            posx_percent = all_bar_lines[i][0] / PAGE_WIDTH
            posy_percent = (all_bar_lines[i][1] - STAFF_HEIGHT/2) / PAGE_HEIGHT
            all_bar_lines[i] = (posx_percent, posy_percent, line_number)

            # Update list that tells where each line starts and ends
            if posy_percent < top_of_line:
                bar_line_positions.append(temp_line_positions)
                temp_line_positions = []
                top_of_line = 0
            elif posy_percent > top_of_line:
                line_position = (posy_percent, posy_percent + STAFF_HEIGHT/PAGE_HEIGHT)
                temp_line_positions.append(line_position)
                top_of_line = posy_percent
            
    # If any of the PS variables are still zero, we have a problem. Exit.
    except ZeroDivisionError, e:
        sys.exit(1)

    bar_line_positions.append(temp_line_positions)
    return all_bar_lines, bar_line_positions

def barlines_to_measures(bar_lines):
    '''Takes in a list of tuples that tell us where bar lines are and which
    line they correspond to. Returns a list of "measures" in the form
      (x coord, y coord, delta x, line number).'''
    measures = []
    for i in range(len(bar_lines)-1):
        if bar_lines[i][2] == bar_lines[i+1][2]:
            delta_x = bar_lines[i+1][0] - bar_lines[i][0]
            measure_data = (bar_lines[i][0],bar_lines[i][1], delta_x,bar_lines[i][2])
            measures.append(measure_data)
        
    return measures

if __name__ == '__main__':
    parse_postscript("march.ps")
