#!/usr/bin/env python
###############################################################
# 
# QUick And Dirty SMS Tilemap Editor 
# 
# (c) Aypok 2006 - 2011
# 
# Contact: tilemapeditor )at( aypok ]D0t[ co {d0T} uk
#          http://twitter.com/Aypok
#          http://www.aypok.co.uk/
# 
###############################################################
# 
# Released under the GNU/GPL v2. See "licence" for more info.
# 
# Thanks: Moobert    - For load of help with all the GTK stuff.
#         SMS Power! - For their SMS VDP documentation.
#                      (http://www.smspower.org/)
# 
###############################################################



# Normal includes.
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import string
from copy import deepcopy
import Image



###############################################################
###############################################################
# 
# Imports an image (PNG, JPEG, GIF, BMP, etc), converts it to
# 16 colours, resizes it, then cuts it into 8x8 tiles (which it
# makes into XPMs and pixmaps) and builds a tilemap for it.
# 
# The data is then loaded into the tilemap editor and shown for
# the user to use.
# 
###############################################################
###############################################################
class image_import:
    def __init__(self):
        return
    
    
    
    ###############################################################
    # Different images are handled in different ways. Some images
    # are not handled at all.
    ###############################################################
    def check_format(self):
        # JPEG or BMP? Handled fine.
        if self.image_file.format == "JPEG" or self.image_file.format == "BMP":
            return True
        
        # PNG or GIF? Handled, but need to alter first.
        if self.image_file.format == "PNG" or self.image_file.format == "GIF":
            self.image_file = self.image_file.convert("RGB")
            return True
        
        # Other image types are not handled.
        print "This image type is not handled, sorry."
        return False
    
    
    
    ###############################################################
    # Sets up the class for an image import.
    ###############################################################
    def setup_class(self, source_file, bright):
        self.image_file = Image.open(source_file)
        if not self.check_format():
            return False
        
        self.new_image  = []
        self.palette    = []
        self.force_pal  = []
        self.bright     = bright
        
        # Crop to a multiple of 8. Shrink, don't expand.
        self.width  = ((self.image_file.size[0] / 8) * 8)
        self.height = ((self.image_file.size[1] / 8) * 8)
        if self.image_file.size[0] > self.width or self.image_file.size[1] > self.height:
            crop_data = (0, 0, self.width, self.height)
            self.image_file = self.image_file.crop(crop_data)
            self.image_file.load()
            self.width  = ((self.image_file.size[0] / 8) * 8)
            self.height = ((self.image_file.size[1] / 8) * 8)
        self.image_data = list(self.image_file.getdata())
        
        return True
    
    
    
    ###############################################################
    # Checks if the value "needle" is in the array "haystack". If
    # it isn't, it adds it. If it is, it adds to the frequency
    # count, so we know how many times each colour occurs.
    ###############################################################
    def in_array(self, needle, haystack):
        for i in range(0, len(haystack)):
            if haystack[i][1] == needle:
                haystack[i][0] += 1
                return True
        haystack.append([1, needle])
        return True
    
    
    
    ###############################################################
    # Changes the colours in the image to SMS compatable colours,
    # then keeps the most common 16 colours. The ones which are
    # scrapped are replaced with the nearest colour out of the ones
    # which are kept.
    ###############################################################
    def sort_out_the_palette(self):
        # Do they want the image darkened or lightened?
        if self.bright:
            max_one = 86
            max_two = 128
        else:
            max_one = 128
            max_two = 212
        
        # Change the colours to SMS compatable ones.
        for i in range(0, len(self.image_data)):
            pixel = [0, 0, 0]
            for j in range(0, 3):
                if self.image_data[i][j] < 43:
                    pixel[j] = 0
                elif self.image_data[i][j] < max_one:
                    pixel[j] = 85
                elif self.image_data[i][j] < max_two:
                    pixel[j] = 170
                else:
                    pixel[j] = 255
            self.new_image.append((pixel[0], pixel[1], pixel[2]))
            self.in_array([pixel[0], pixel[1], pixel[2]], self.palette)
        
        # Sort palette from most common to most uncommon colours. Then split the 16 most common
        # colours into a seperate list, so we can keep them.
        self.palette.sort()
        self.palette.reverse()
        old_colours = self.palette[16:]
        self.palette = self.palette[:16]
        
        # Replace the frequency counts with the colour sums.
        for i in range(0, len(self.palette)):
            self.palette[i][0] = (self.palette[i][1][0] * 16) + (self.palette[i][1][1] * 4) + self.palette[i][1][2]
        for i in range(0, len(old_colours)):
            old_colours[i][0] = (old_colours[i][1][0] * 16) + (old_colours[i][1][1] * 4) + old_colours[i][1][2]
        
        # Find the closest colour in palette to all those in old_colours.
        for i in range(0, len(old_colours)):
            closest = []
            for j in range(0, len(self.palette)):
                value = self.palette[j][0] - old_colours[i][0]
                if value < 0:
                    value *= -1
                closest.append([value, j])
            # Replace the old_colour's has with the index of the closest colour in palette.
            closest.sort()
            old_colours[i][0] = closest[0][1]
        
        # Replace all old_colours with the closest colour in palette. Reduce to 16 colours.
        if len(old_colours) > 0:
            self.image_data = self.new_image
            self.new_image = []
            for i in range(0, len(self.image_data)):
                written = 0
                for j in range(0, len(old_colours)):
                    if self.image_data[i][0] == old_colours[j][1][0] and self.image_data[i][1] == old_colours[j][1][1] and self.image_data[i][2] == old_colours[j][1][2]:
                        self.new_image.append((self.palette[old_colours[j][0]][1][0], self.palette[old_colours[j][0]][1][1], self.palette[old_colours[j][0]][1][2]))
                        written = 1
                if not written:
                    self.new_image.append(self.image_data[i])
        
        # Remove the colour hashes.
        for i in range(0, len(self.palette)):
            self.palette[i] = (self.palette[i][1][0], self.palette[i][1][1], self.palette[i][1][2])
        
        return True
    
    
    
    ###############################################################
    # Builds the base XPM tiles from the image and removes all
    # duplicate tiles. It also builds a tilemap for the image from
    # these tiles.
    ###############################################################
    def build_xpms_and_tilemap(self):
        # Convert to 8x8 XPM blocks.
        temp_tiles = []
        for y in range(0, self.height, 8):
            for x in range(0, self.width, 8):
                tile = []
                for yy in range(0, 8):
                    line = ""
                    #text = ""
                    for xx in range(0, 8):
                        line += chr(97 + self.palette.index(self.new_image[(((y + yy) * self.width) + (x + xx))]))
                        #text += str(((y + yy) * self.width) + (x + xx)) + ", "
                    tile.append(line)
                    #print text
                temp_tiles.append(tile)
        #print "Tiles: " + str(len(temp_tiles))
        
        # Build a basic tilemap.
        tilemap_list = []
        for i in range(0, len(temp_tiles)):
            tilemap_list.append([i, 0])
        
        # Create a list of unique tiles.
        unique_tiles = []
        for i in range(0, len(temp_tiles)):
            try:
                unique_tiles.index(temp_tiles[i])
            except ValueError:
                unique_tiles.append(temp_tiles[i])
        
        # The SMS only has enough VRAM for 512 tiles. Well, some of that is
        # used for sprites and stuff. Warn the user if there are too many.
        # TODO: Make this in to a pop-up sort of "OMG! Error!" thing.
        if len(unique_tiles) > 512:
            print "There are " + str(len(unique_tiles)) + " unique tiles. The SMS can only handle 512, so the image will not display correctly."
        
        # Update the tilemap.
        for i in range(0, len(tilemap_list)):
            tilemap_list[i] = [unique_tiles.index(temp_tiles[i]), 0]
        
        return unique_tiles, tilemap_list
    
    
    
    ###############################################################
    # Sort out the palette. Change the data to hex hashes for
    # the XPMs to use.
    ###############################################################
    def final_palette_adjustments(self):
        palette.xpm_tile_palette = ["8 8 " + str(len(self.palette)) + " 1"]
        for i in range(0, len(self.palette)):
            line = chr(i + 97) + " c #"
            colour = ""
            for j in range(0, 3):
                value = hex(self.palette[i][j])[2:]
                if value == "0":
                    value = "00"
                line += value
                colour += value
            palette.xpm_tile_palette.append(line)
            self.palette[i] = colour
        
        # Find the numbers of these colours from the palette list
        # in the "palette" class, then set the palette numbers for
        # the user.
        for i in range(0, len(self.palette)):
            palette.palette[i] = palette.colour_lookup.index(self.palette[i])
        if len(self.palette) < 16:
            for i in range(len(self.palette), 16):
                palette.palette[i] = 0
        
        # Update the input boxen on the palette window.
        pal_tiles  = ""
        pal_sprite = ""
        for i in range(0, 16):
            if pal_tiles != "":
                pal_tiles += ","
            pal_tiles += str(palette.palette[i])
        for i in range(16, 32):
            if pal_sprite != "":
                pal_sprite += ","
            pal_sprite += str(palette.palette[i])
        
        # Update the palette entry boxen.
        gtk_thing.entry_set_palette_tile.set_text(pal_tiles)
        gtk_thing.entry_set_palette_sprite.set_text(pal_sprite)
        
        return True
    
    
    
    ###############################################################
    # Builds all the different XPMs from the tiles made from the
    # image, then convert them to pixmaps for the tilemap editor
    # to use.
    ###############################################################
    def builds_xpms_and_pixmaps(self):
        # Clear tiles.
        tiles.xpm_tiles    = [[], [], []]
        tiles.pixmap_tiles = [[], [], []]
        tiles.pixmap_masks = [[], [], []]
        
        for xpm_tile_temp in self.temp_tiles:
            tiles.xpm_tiles[1].append(tiles.make_tile_zoom(xpm_tile_temp, 2))
            tiles.xpm_tiles[2].append(tiles.make_tile_zoom(xpm_tile_temp, 4))
            tiles.xpm_tiles[0].append(palette.xpm_tile_palette + xpm_tile_temp)
        
        # No more that 512 tiles.
        tiles.xpm_tiles[0] = tiles.xpm_tiles[0][:512]
        tiles.xpm_tiles[1] = tiles.xpm_tiles[1][:512]
        tiles.xpm_tiles[2] = tiles.xpm_tiles[2][:512]
        
        # Convert to pixmaps.
        tiles.xmp_to_pixmaps(gtk_thing.window.window, 0)
        gtk_thing.area_tile_expose_cb(0, 0)
        
        return True
    
    
    
    ###############################################################
    # Loads the image specified in "source_file", resizes it,
    # converts it to 16 colours, then splits the image into tiles
    # and builds a tilemap for it.
    ###############################################################
    def load_and_convert(self):
        # Do all the initial palette and colour manipulation needed.
        self.sort_out_the_palette()
        
        # Builds the base XPMs/tiles and a tilemap.
        self.temp_tiles, self.tilemap_list = list(self.build_xpms_and_tilemap())
        print "Tiles kept: " + str(len(self.temp_tiles))
        
        
        
        # Finish up the tilemap.
        world = []
        for y in range(0, (self.height / 8)):
            world.append(self.tilemap_list[(y * (self.width / 8)):((y * (self.width / 8)) + (self.width / 8))])
        #for line in world:
        #    print line
        
        
        
        # Sort out the palette. Change the data to hex hashes for
        # the XPMs to use.
        self.final_palette_adjustments()
        
        # Build all the different XPMs needed, and convert them to pixmaps.
        self.builds_xpms_and_pixmaps()
        
        # Give the tilemap to the main part of the editor.
        tilemap.world = []
        tilemap.reorientate_tilemap(world)
        gtk_thing.area_map.window.clear()
        gtk_thing.area_map_expose_cb(0, 0)
        
        return True
    
    
    
    ###############################################################
    # Update and show the image.
    ###############################################################
    def update_and_show_image(self):
        self.image_file.putdata(self.new_image, 1.0, 0.0)
        self.image_file.show()
        return True
    
    
    
    ###############################################################
    # Cleans up after an image import.
    ###############################################################
    def all_done_mon_capitan(self):
        self.image_file = 0
        self.image_data = 0
        self.new_image  = 0
        return True






###############################################################
###############################################################
# 
# Sorts out and stores the palettes
# 
###############################################################
###############################################################
class palettes_and_colours:
    def __init__(self):
        # Palettes.
        #self.palette            = [0,1,2,3,4,8,12,32,48,56,10,15,31,63,42,21,
        #                           0,12,8,0,6,21,42,43,15,48,3,0,0,63,0,0]
        self.palette            = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                                   0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.xpm_tile_palette   = []        # The start of each tile XPM.
        self.xpm_sprite_palette = []        # The start of each sprite XPM.
        
        self.colour_lookup      = [         # Lookup list of all 64 SMS colours.
            "000000", "550000", "aa0000", "ff0000",
            "005500", "555500", "aa5500", "ff5500",
            "00aa00", "55aa00", "aaaa00", "ffaa00",
            "00ff00", "55ff00", "aaff00", "ffff00",
            "000055", "550055", "aa0055", "ff0055",
            "005555", "555555", "aa5555", "ff5555",
            "00aa55", "55aa55", "aaaa55", "ffaa55",
            "00ff55", "55ff55", "aaff55", "ffff55",
            "0000aa", "5500aa", "aa00aa", "ff00aa",
            "0055aa", "5555aa", "aa55aa", "ff55aa",
            "00aaaa", "55aaaa", "aaaaaa", "ffaaaa",
            "00ffaa", "55ffaa", "aaffaa", "ffffaa",
            "0000ff", "5500ff", "aa00ff", "ff00ff",
            "0055ff", "5555ff", "aa55ff", "ff55ff",
            "00aaff", "55aaff", "aaaaff", "ffaaff",
            "00ffff", "55ffff", "aaffff", "ffffff"]
        
        # Build the XPM palette data.
        self.set_xpm_palettes()
    
    
    
    ###############################################################
    # Sets the palette to the new data given by the user.
    ###############################################################
    def set_palette(self):
        self.palette = []
        
        # Check the user's input.
        pal_ret_tile   = self.fill_palette(0)
        pal_ret_sprite = self.fill_palette(1)
        if pal_ret_tile != True:
            gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
            gtk_thing.statusbar.push(gtk_thing.statusbar_context, "'" + str(pal_ret_tile) + "' isn't in the range 0-63.")
            return False
        if pal_ret_sprite != True:
            gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
            gtk_thing.statusbar.push(gtk_thing.statusbar_context, "'" + str(pal_ret_sprite) + "' isn't in the range 0-63.")
            return False
        
        self.set_xpm_palettes()
        
        # Tile and sprite palette output.
        pal_tiles  = ""
        pal_sprite = ""
        for i in range(0, 16):
            if pal_tiles != "":
                pal_tiles += ","
            pal_tiles += str(self.palette[i])
        for i in range(16, 32):
            if pal_sprite != "":
                pal_sprite += ","
            pal_sprite += str(self.palette[i])
        
        # Update the XPMs.
        self.update_xpms_palettes()
        
        # Update the palette entry boxen.
        gtk_thing.entry_set_palette_tile.set_text(pal_tiles)
        gtk_thing.entry_set_palette_sprite.set_text(pal_sprite)
        
        # Update the status bar.
        gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
        gtk_thing.statusbar.push(gtk_thing.statusbar_context, "Palette Modified.")
        gtk_thing.window_set_palette.hide()
        return True
    
    
    
    ###############################################################
    # Update the XPM palette lists.
    ###############################################################
    def set_xpm_palettes(self):
        self.xpm_tile_palette = [
            "8 8 16 1",
            "a c #" + self.colour_lookup[self.palette[0]],  "b c #" + self.colour_lookup[self.palette[1]],
            "c c #" + self.colour_lookup[self.palette[2]],  "d c #" + self.colour_lookup[self.palette[3]],
            "e c #" + self.colour_lookup[self.palette[4]],  "f c #" + self.colour_lookup[self.palette[5]],
            "g c #" + self.colour_lookup[self.palette[6]],  "h c #" + self.colour_lookup[self.palette[7]],
            "i c #" + self.colour_lookup[self.palette[8]],  "j c #" + self.colour_lookup[self.palette[9]],
            "k c #" + self.colour_lookup[self.palette[10]], "l c #" + self.colour_lookup[self.palette[11]],
            "m c #" + self.colour_lookup[self.palette[12]], "n c #" + self.colour_lookup[self.palette[13]],
            "o c #" + self.colour_lookup[self.palette[14]], "p c #" + self.colour_lookup[self.palette[15]]]
        
        self.xpm_sprite_palette = [
            "8 8 16 1",
            "a c #" + self.colour_lookup[self.palette[16]], "b c #" + self.colour_lookup[self.palette[17]],
            "c c #" + self.colour_lookup[self.palette[18]], "d c #" + self.colour_lookup[self.palette[19]],
            "e c #" + self.colour_lookup[self.palette[20]], "f c #" + self.colour_lookup[self.palette[21]],
            "g c #" + self.colour_lookup[self.palette[22]], "h c #" + self.colour_lookup[self.palette[23]],
            "i c #" + self.colour_lookup[self.palette[24]], "j c #" + self.colour_lookup[self.palette[25]],
            "k c #" + self.colour_lookup[self.palette[26]], "l c #" + self.colour_lookup[self.palette[27]],
            "m c #" + self.colour_lookup[self.palette[28]], "n c #" + self.colour_lookup[self.palette[29]],
            "o c #" + self.colour_lookup[self.palette[30]], "p c #" + self.colour_lookup[self.palette[31]]]
        return
    
    
    
    ###############################################################
    # "palette_type" 1 = sprite, 0 = tile.
    ###############################################################
    def fill_palette(self, palette_type):
        if not palette_type:
            palette_temp = gtk_thing.entry_set_palette_tile.get_text().strip().split(",")
            max_len = 16
        else:
            palette_temp = gtk_thing.entry_set_palette_sprite.get_text().strip().split(",")
            max_len = 32
        
        # Fill the palette
        for colour in palette_temp:
            if colour == "":
                continue
            # Hex?
            if colour[:1] == "$":
                colour = "0x" + colour[1:]
                colour = int(colour, 16)        # Do "try" checking stuff here and catch "ValueError".
            else:
                colour = int(colour)
            
            # Check it's in range.
            if colour > 63 or colour < 0:
                return colour
            self.palette.append(colour)
        
        # Make sure we have the right amount of colours colours - no more, no less.
        if len(self.palette) < max_len:
            for i in range(0, (max_len - len(self.palette))):
                self.palette.append(0)
        self.palette = self.palette[:max_len]
        return True
    
    
    
    ###############################################################
    # Replaces the current palette data in all XPMs with the new
    # data.
    ###############################################################
    def update_xpms_palettes(self):
        for j in range(0, 3):
            for i in range(0, len(tiles.xpm_tiles[j])):
                for k in range(1, 17):
                    tiles.xpm_tiles[j][i][k] = self.xpm_tile_palette[k]
        
        # Update the pixmaps.
        tiles.pixmap_tiles = [[], [], []]
        tiles.pixmap_masks = [[], [], []]
        tiles.xmp_to_pixmaps(gtk_thing.window.window)
        
        # Update the display.
        gtk_thing.area_map_expose_cb(0, 0)
        gtk_thing.area_tile_expose_cb(0, 0)
        gtk_thing.image_selected_tile.set_from_pixmap(tiles.pixmap_tiles[2][tiles.selected_tile], tiles.pixmap_masks[2][tiles.selected_tile])
        return






###############################################################
###############################################################
# 
# Stores the tilemap data and contains functions for resizing
# it, etc.
# 
###############################################################
###############################################################
class tilemap_things_and_such:
    def __init__(self):
        self.width  = 32                # Width, in tiles, of map.
        self.height = 24                # Height, in tiles, of map.
        
        self.bytes_per_line = 32        # For exporting data.
        self.data_format    = 0         # 0 = hex, 1 = dec, 2 = bin.
        self.inc_byte_two   = 0         # 0 = no, 1 = yes.
        self.byte_or_word   = 0         # 0 = byte, 1 = word.
        self.flip_rotate    = 0         # 0 = no, 1 = yes.
        
        self.undo_list = []             # Keeps a list of tile placings.
        self.redo_list = []             # Keeps a list of undone tile placings.
    
    
    
    ###############################################################
    # Create a new, blank tilemap.
    ###############################################################
    def new(self):
        # Create the default empty 32x24 tilemap.
        # self.world[x][y][z] - z == 0 for tile number, 1 for second byte
        self.world  = []
        outter      = []
        for i in range(0, self.height):
            outter.append([0, 0])
        for i in range(0, self.width):
            self.world.append(deepcopy(outter))
        del outter
        
        # Set some values for the new tilemap.
        self.changed = 0                # Whether or not the tilemap has been changed.
        self.start   = [0, 0]           # Top left point (tile) shown.
        
        gtk_thing.update_label_area_shown_data()
        gtk_thing.reset_tilemap_scrollbars()
        gtk_thing.sort_out_tilemap_scrollbars()
        gtk_thing.area_map.window.clear()
        gtk_thing.area_map_expose_cb(0, 0)
        gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
        gtk_thing.statusbar.push(gtk_thing.statusbar_context, "New " + str(self.width) + "x" + str(self.height) + " tilemap created.")
        return
    
    
    
    ###############################################################
    # Exports the tilemap data to the specified file in the
    # specified format.
    ###############################################################
    def export_data(self, object, event = 0):
        #print "exporting data: format = " + str(self.data_format) + " and bytes per line = " + str(self.bytes_per_line)
        file_name = gtk_thing.entry_export_tilemap_filename.get_text()
        
        # If they want the data flipped and rotated, we backup the current
        # world list, then change the actual list. This saves having too
        # much extra code for it. Once done, the backup list is copied back.
        if self.flip_rotate:
            self.flipping_world()
            
        # Choose the data format.
        if self.data_format == 0 or self.data_format == 1:
            self.export_data_hex_dec(file_name)
        if self.data_format == 2:
            self.export_data_bin(file_name)
        
        # Revert to the backup world, if needed.
        if self.flip_rotate:
            self.world = deepcopy(self.world_backup)
            del self.world_backup
            
            # Swap the height and width values, since the tilemap was rotated.
            old_width = self.width
            self.width = self.height
            self.height = old_width
        
        gtk_thing.window_export_tilemap.hide()
        gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
        gtk_thing.statusbar.push(gtk_thing.statusbar_context, "Successfully exported the tilemap to '" + file_name + "'.")
        return True
    
    
    
    # Backs up the world list and then rotates the data. The way it's
    # stored is flipped, so we don't need to do that.
    def flipping_world(self):
        self.world_backup = deepcopy(self.world)
        brave_new_world   = []
        brave_new_row     = []
        
        # Now to "rotate" it. This is the tricky part.
        #
        # Convert from this:
        #   y0    y1    y2    y3
        # [[00], [04], [08], [12]] x0
        # [[01], [05], [09], [13]] x1
        # [[02], [06], [10], [14]] x2
        # [[03], [07], [11], [15]] x3
        # 
        # To this:
        # [[03], [02], [01], [00]] y0
        # [[07], [06], [05], [04]] y1
        # [[11], [10], [09], [08]] y2
        # [[15], [14], [13], [12]] y3
        #   x3    x2    x1    x0
        for y in range(0, self.height):
            for x in range(0, self.width):
                brave_new_row.append(deepcopy(self.world[x][y]))
            brave_new_world.append(deepcopy(brave_new_row))
            brave_new_row = []
        self.world = deepcopy(brave_new_world)
        del brave_new_world, brave_new_row
        
        # Swap the height and width values, since the tilemap was rotated.
        old_width = self.width
        self.width = self.height
        self.height = old_width
        self.bytes_per_line = self.width
        
        return
    
    
    
    # Exports the map data in hex or dec format. EG:
    # .db $00,$74,$4e,$89   (hex)
    # .db 0,116,78,137      (dec)
    def export_data_hex_dec(self, file_name):
        export_file = open(file_name, "w")
        for y in range(0, self.height):
            if self.byte_or_word:
                line = ".dw "
            else:
                line = ".db "
            
            # Loop through data.
            for x in range(0, self.bytes_per_line):     # Cuts off extra. Need to wrap around.
                if line != ".db " and line != ".dw ":
                    line += ","
                
                # Write data as hex or dec?
                if not self.data_format:
                    line += "$"
                    if self.byte_or_word:
                        # Write data as hexidecimal word.
                        if self.inc_byte_two:
                            value = self.world[x][y][0]|(self.world[x][y][1]<<8)
                        else:
                            value = self.world[x][y][0]
                            
                        # Pad it with zeros.
                        if value < 4096:
                            line += "0"
                        if value < 256:
                            line += "0"
                        if value < 16:
                            line += "0"
                        line += str(hex(value))[2:]
                    else:
                        # Write data as hexidecimal byte(s).
                        #print "x: " + str(x) + " y: " + str(y)
                        if self.world[x][y][0] < 16:
                            line += "0"
                        line += str(hex(self.world[x][y][0]))[2:]
                        if self.inc_byte_two:
                            line += ",$"
                            if self.world[x][y][1] < 16:
                                line += "0"
                            line += str(hex(self.world[x][y][1]))[2:]
                else:
                    if self.byte_or_word:
                        # Write data as decimal word.
                        if self.inc_byte_two:
                            line += str(self.world[x][y][0]|(self.world[x][y][1]<<8))
                        else:
                            line += str(self.world[x][y][0])
                    else:
                        # Write data as decimal byte(s).
                        line += str(self.world[x][y][0])
                        if self.inc_byte_two:
                            line += "," + str(self.world[x][y][1])
            
            export_file.write(line + "\n")
        export_file.close()
        return
    
    # Exports the map data as a binary file (not text).
    def export_data_bin(self, file_name):
        export_file = open(file_name, "wb")
        for y in range(0, self.height):
            for x in range(0, self.bytes_per_line):     # Cuts of extra. Need to wrap around.
                if self.inc_byte_two:
                    export_file.write(chr(self.world[x][y][0]|(self.world[x][y][1]<<8)))
                else:
                    export_file.write(chr(self.world[x][y][0]))
            export_file.flush()
        export_file.close()
        return
    
    
    ###############################################################
    # Sort out the export settings.
    ###############################################################
    # Set the number of bytes of map to write per line of the
    # exported file.
    def set_bytes_per_line_8(self, object, event = 0):
        self.bytes_per_line = 8
        return True
    def set_bytes_per_line_16(self, object, event = 0):
        self.bytes_per_line = 16
        return True
    def set_bytes_per_line_32(self, object, event = 0):
        self.bytes_per_line = 32
        return True
    def set_bytes_per_line_64(self, object, event = 0):
        self.bytes_per_line = 64
        return True
    def set_bytes_per_line_128(self, object, event = 0):
        self.bytes_per_line = 128
        return True
    def set_bytes_per_line_256(self, object, event = 0):
        self.bytes_per_line = 256
        return True
    def set_bytes_per_line_full(self, object, event = 0):
        self.bytes_per_line = self.width
        return True
    
    # Sets the data format to use for the data export.
    def set_data_format_hex(self, object, event = 0):
        self.data_format = 0
        return True
    def set_data_format_dec(self, object, event = 0):
        self.data_format = 1
        return True
    def set_data_format_bin(self, object, event = 0):
        self.data_format = 2
        return True
    
    # Sets whether or not to export the extra tile data, like flipping.
    def set_one_byte_tiles(self, object, event = 0):
        self.inc_byte_two = 0
        return True
    def set_two_byte_tiles(self, object, event = 0):
        self.inc_byte_two = 1
        return True
    
    # Sets whether to write the data as bytes or words.
    def set_write_as_bytes(self, object, event = 0):
        # Run throught all tile numbers and see if any can't be
        # written as a byte. IE; those over 255.
        
        self.byte_or_word = 0
        return True
    def set_write_as_words(self, object, event = 0):
        self.byte_or_word = 1
        return True
    
    # Set whether to flip and rotate the tilemap data.
    def set_flip_rotate_off(self, object, event = 0):
        self.flip_rotate = 0
        return True
    
    def set_flip_rotate_on(self, object, event = 0):
        self.flip_rotate = 1
        return True
    
    
    
    ###############################################################
    # Resizes the tilemap to the values given in
    # gtk_thing.window_resize_tilemap's entry boxen.
    ###############################################################
    def resize_tilemap(self):
        new_width  = int(gtk_thing.entry_resize_tilemap_width.get_text())
        new_height = int(gtk_thing.entry_resize_tilemap_height.get_text())
        
        # Shrink the height.
        if new_height < self.height:
            for i in range(0, self.width):
                self.world[i] = self.world[i][:new_height]
         
        # Expand the height.
        if new_height > self.height:
            for i in range(0, self.width):
                for j in range(0, (new_height - self.height)):
                    self.world[i].append([0, 0])
        
        # Shrink the width.
        if new_width < self.width:
            self.world = self.world[:new_width]
        
        # Expand the width.
        if new_width > self.width:
            outter = []
            for i in range(0, new_height):
                outter.append([0, 0])
            for i in range(0, (new_width - self.width)):
                self.world.append(deepcopy(outter))
            del outter
        
        self.width  = new_width
        self.height = new_height
        self.bytes_per_line = new_width
        
        # Update the status bar and display.
        gtk_thing.update_label_area_shown_data()
        gtk_thing.update_label_area_total()
        gtk_thing.sort_out_tilemap_scrollbars()
        gtk_thing.area_map.window.clear()
        gtk_thing.area_map_expose_cb(0, 0)
        gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
        gtk_thing.statusbar.push(gtk_thing.statusbar_context, "Changed the tilemap's size to " + str(self.width) + "x" + str(self.height) + ".")
        return
    
    
    
    ###############################################################
    # The world is currently the wrong way around: temp_world[y][x]
    # instead of the proper way: temp_world[x][y]. So we need to
    # correct that.
    ###############################################################
    def reorientate_tilemap(self, temp_world):
        for y in range(0, len(temp_world[0])):
            col = []
            for x in range(0, len(temp_world)):
                col.append(deepcopy(temp_world[x][y]))
            self.world.append(deepcopy(col))
        
        # Set the dimensions for the new tilemap
        self.width  = len(self.world)
        self.height = len(self.world[0])
        
        return True
    
    
    
    ###############################################################
    # Imports a tilemap from a file.
    ###############################################################
    def import_tilemap(self, source_file, flip_rotate = 0):
        # Open the file containing the tile data.
        file_tilemap_input = open(source_file, "r")
        tilemap_source = file_tilemap_input.readlines()
        file_tilemap_input.close()
        temp_world = []
        self.world = []
        
        # Loop through all lines in the tile data file.
        for line in tilemap_source:
            tilemap_row = []
            
            # Do we know what to do with this line? No? Skip it.
            if line.lower()[:3] != ".db" and line.lower()[:3] != ".dw":
                continue
            
            # Split up the tilemap row into individual bytes/words.
            line = line[4:].strip()
            if line[:1] == "$":
                is_hex = 1
                line = line.replace("$", "")
            else:
                is_hex = 0
            line = line.split(",")
            
            # Loop through every byte listed.
            for tile in line:
                # Get the value.
                if is_hex:
                    value = int(("0x" + tile), 16)
                else:
                    value = int(tile)
                
                # Store the value.
                # value&511  == lower nine bits (tile number).
                # value&7680 == higher four bits (tile mode).
                tilemap_row.append([(value&511), (value&7680)])
            temp_world.append(deepcopy(tilemap_row))
        
        # Fix the tilemap orientation.
        if not flip_rotate:
            self.reorientate_tilemap(temp_world)
        else:
            self.world  = deepcopy(temp_world)
            self.width  = len(self.world)
            self.height = len(self.world[0])
        gtk_thing.sort_out_tilemap_scrollbars()
        
        return True





###############################################################
###############################################################
#
# Handles to creation of XPMs from raw tile data and stores
# them in jars.
#
###############################################################
###############################################################
class create_tiles:
    def __init__(self):
        self.selected_tile    = 0       # Default selected tile is 0.
        self.pixmap           = ""      # Current pixmap.
        self.zoom             = 0       # Zoom level. 0, 1, or 2.
        self.mode             = 0       # Mode, for flipping, etc.
        
        # XPMs. self.xpm_tiles[0] = 8x8, [1] = 16x16, [2] = 32x32.
        self.xpm_tiles        = [[0], [0], [0]]
        
        # Pixmaps. self.pixmap_tiles[0] = 8x8, [1] = 16x16, [2] = 32x32.
        self.pixmap_tiles     = [[], [], []]
        
        # Pixmap masks. self.pixmap_masks[0] = 8x8, [1] = 16x16, [2] = 32x32.
        self.pixmap_masks     = [[], [], []]
        
        # Create an empty tile to use until the user loads their own.
        self.create_blank_tile()
    
    
    
    ###############################################################
    # Loads tiles from the "source_file" and converts them to XPMs
    # over two stages.
    ###############################################################
    def load_tiles_and_make_xpms(self, source_file):
        # Open the file containing the tile data.
        file_tiles_input = open(source_file, "r")
        tile_source = file_tiles_input.readlines()
        file_tiles_input.close()
        
        # Loop through all lines in the tile data file.
        for tile_current in tile_source:
            tile_final = []
            
            # It is a commented line? Skip it.
            if tile_current[:1] == ";":
                continue
                
            # Split the tile up into individual bytes.
            tile_current = tile_current[4:].strip().replace("$", "").split(",")
            
            # Loop through all bytes in the tile, four at a time.
            # Each line of pixels is four bytes. Stage one.
            for i in range(0, 32, 4):
                for j in (128, 64, 32, 16, 8, 4, 2, 1):                     # Go through all eight bits of the byte.
                    nibble = 0                                              # Initialize the nibble.
                    for k in range(0, 4):                                   # We check the first bit of each four bytes, then the second, etc.
                        if j&string.atoi(tile_current[i + k], 16) == j:     # We find out if a bit in the byte is set by ANDing it with 'j',
                            nibble += 2**k                                  # If it's set, we need to update "nibble".
                    tile_final.append(nibble)                               # Store it and go onto the next nibble of the tile.
            
            # Pixmap data. Stage two.
            xpm_tile_temp = []
            for i in range(0, 64, 8):
                line = ""
                for j in range(0, 8):
                    line += chr(tile_final[i + j] + 97)                     # Convert it to an ASCII character.
                xpm_tile_temp.append(line)
            self.xpm_tiles[1].append(self.make_tile_zoom(xpm_tile_temp, 2))
            self.xpm_tiles[2].append(self.make_tile_zoom(xpm_tile_temp, 4))
            self.xpm_tiles[0].append(palette.xpm_tile_palette + xpm_tile_temp)
        
        # No more that 512 tiles.
        self.xpm_tiles[0] = self.xpm_tiles[0][:512]
        self.xpm_tiles[1] = self.xpm_tiles[1][:512]
        self.xpm_tiles[2] = self.xpm_tiles[2][:512]
        return True
    
    
    
    ###############################################################
    # Overwrites current tiles with new ones in "source_file".
    ###############################################################
    def load_tiles_and_overwrite(self, source_file):
        self.pixmap       = ""
        self.xpm_tiles    = [[], [], []]
        self.pixmap_tiles = [[], [], []]
        self.pixmap_masks = [[], [], []]
        
        self.load_tiles_and_make_xpms(source_file)
        return True
    
    
    
    ###############################################################
    # Converts the XPMs to a useable pixmap format for GTK.
    ###############################################################
    def xmp_to_pixmaps(self, window, start = 0):
        # Unzoomed - 8x8.
        for i in range(start, len(self.xpm_tiles[0])):
            pixmap, mask = gtk.gdk.pixmap_create_from_xpm_d(window, None, self.xpm_tiles[0][i])
            self.pixmap_tiles[0].append(pixmap)
            self.pixmap_masks[0].append(mask)
        # Zoomed - 16x16.
        for i in range(start, len(self.xpm_tiles[1])):
            pixmap, mask = gtk.gdk.pixmap_create_from_xpm_d(window, None, self.xpm_tiles[1][i])
            self.pixmap_tiles[1].append(pixmap)
            self.pixmap_masks[1].append(mask)
        # Zoomed - 32x32.
        for i in range(start, len(self.xpm_tiles[1])):
            pixmap, mask = gtk.gdk.pixmap_create_from_xpm_d(window, None, self.xpm_tiles[2][i])
            self.pixmap_tiles[2].append(pixmap)
            self.pixmap_masks[2].append(mask)
        return
    
    
    
    ###############################################################
    # Changes size of the pixmap given to it in "xpm".
    # The size is given in "zoom". If it's "2", it will double the
    # size, etc.
    ###############################################################
    def make_tile_zoom(self, xpm, zoom):
        xpm_tile_temp = []
        
        for line in xpm:
            out_line = ""
            for i in line:
                out_line += i*zoom
            for i in range(0, zoom):
                xpm_tile_temp.append(out_line)
        
        # Add the palette, change the size in the palette, then return.
        xpm_tile_temp = palette.xpm_tile_palette + xpm_tile_temp
        xpm_tile_temp[0] = xpm_tile_temp[0].replace("8 8", (str(8 * zoom) + " " + str(8 * zoom)))
        return xpm_tile_temp
    
    
    
    ###############################################################
    # Sets the selected tile to the tile in "clicked".
    ###############################################################
    def set_selected_tile(self, clicked):
        self.selected_tile = clicked
        # If they clicked on something other than a tile, set it to tile 0.
        if self.selected_tile >= len(self.pixmap_tiles[0]):
            self.selected_tile = 0
        #self.pixmap = self.pixmap_tiles[self.zoom][self.selected_tile]
        
        # Show the tile and tile number in the bit below the tile chooser.
        gtk_thing.label_selected_tile_dec.set_text(str(self.selected_tile))
        gtk_thing.label_selected_tile_hex.set_text(str(hex(self.selected_tile)))
        gtk_thing.image_selected_tile.set_from_pixmap(self.pixmap_tiles[2][self.selected_tile], self.pixmap_masks[2][self.selected_tile])
        return
    
    
    
    ###############################################################
    # Creates a blank tile (and its zoomed versions).
    ###############################################################
    def create_blank_tile(self):
        for i in range(0, 3):
            zoom = 2**i
            xpm_tile_temp = []
            for j in range(0, (zoom * 8)):
                xpm_tile_temp.append("a" * (zoom * 8))
            self.xpm_tiles[i][0] = palette.xpm_tile_palette + xpm_tile_temp
            self.xpm_tiles[i][0][0] = self.xpm_tiles[i][0][0].replace("8 8", (str(8 * zoom) + " " + str(8 * zoom)))
        return
    
    
    
    ###############################################################
    # Sets the various modes for the tiles. When exporting the
    # tilemap, this value (bitshifted left 8 bits) is ORed with the
    # tile number:  output = tile_number|(mode<<8)
    #
    # Tile mode: ---pcvhn
    #
    #            - = Unused.
    #            p = Priority flag.
    #            c = Palette select.
    #            v = Vertical flip flag.
    #            h = Horizontal flip flag.
    #            n = 9th bit of tile number.
    ###############################################################
    # No flipping. XOR with "00000110". Do each bit seperately.
    def set_tile_mode_normal(self, object, event = 0):
        if self.mode&2 == 2:
            self.mode = self.mode^2
        if self.mode&4 == 4:
            self.mode = self.mode^4
        return True
    
    # Enable X flipping. XOR with "00000010".
    def set_tile_mode_x_flip(self, object, event = 0):
        if self.mode&2 != 2:
            self.mode = self.mode^2     # Set X flip.
        if self.mode&6 == 6:
            self.mode = self.mode^4     # Unset Y flip.
        return True
    
    # Enable Y flipping. XOR with "00000100".
    def set_tile_mode_y_flip(self, object, event = 0):
        if self.mode&4 != 4:
            self.mode = self.mode^4     # Set Y flip.
        if self.mode&6 == 6:
            self.mode = self.mode^2     # Unset X flip.
        return True
    
    # Enable X and Y flipping. OR with "00000110".
    def set_tile_mode_xy_flip(self, object, event = 0):
        if self.mode&2 != 2:
            self.mode = self.mode^2
        if self.mode&4 != 4:
            self.mode = self.mode^4
        return True
    
    # Make the tile use the standard tile palette (normal).
    # XOR with "00001000". Unset if set.
    def set_tile_mode_palette_tile(self, object, event = 0):
        if self.mode&8 == 8:
            self.mode = self.mode^8
        return True
    
    # Make the tile use the sprite palette.
    # XOR with "00001000". Set if unset.
    def set_tile_mode_palette_sprite(self, object, event = 0):
        if self.mode&8 != 8:
            self.mode = self.mode^8
        return True
    
    # Make the tile appear behind sprites (normal).
    # XOR with "00010000". Unset if set.
    def set_tile_mode_priority_behind(self, object, event = 0):
        if self.mode&16 == 16:
            self.mode = self.mode^16
        return True
    
    # Make the tile appear infront of sprites.
    #  XOR with "00010000". Set if unset.
    def set_tile_mode_priority_infront(self, object, event = 0):
        if self.mode&16 != 16:
            self.mode = self.mode^16
        return True
    
    
    
    ###############################################################
    # Fills all unused tile-slots (upto 511) with tile zero.
    ###############################################################
    def fill_tiles(self, object, event = 0):
        start = len(self.xpm_tiles[0])
        for i in range(len(self.xpm_tiles[0]), 512):
            self.xpm_tiles[0].append(deepcopy(self.xpm_tiles[0][0]))
            self.xpm_tiles[1].append(deepcopy(self.xpm_tiles[1][0]))
            self.xpm_tiles[2].append(deepcopy(self.xpm_tiles[2][0]))
        self.xmp_to_pixmaps(gtk_thing.window.window, start)
        gtk_thing.area_tile_expose_cb(0, 0)
        return True
    
    
    
    ###############################################################
    # Exports the tiles to a file.
    ###############################################################
    def export_tiles(self, file_name):
        export_file = open(file_name, "w")
        start_pos   = len(self.xpm_tiles[0][0]) - 8
        
        # Loop through all tiles so that we can convert them.
        for i in range(0, len(self.xpm_tiles[0])):
            line = ""
            # We handle two rows at a time, so skip every other one,
            for j in range(start_pos, (start_pos + 8)):
                if line:
                    line += ","
                line_b = ""
                cols   = []
                bytes  = [0, 0, 0, 0]
                
                # Each char/pixel of the row.
                for k in range(0, 8):
                    #print "self.xpm_tiles[0][" + str(i) + "][" + str(j) + "][" + str(k) + "]"
                    cols.append(ord(self.xpm_tiles[0][i][j][k]) - 97)
                
                # Calculate the four bytes for this row.
                for b in range(0, 4):
                    ander = 2**b
                    for a in range(0, 8):
                        bit = (2 ** (8 - a - 1))
                        if cols[a]&ander:
                            bytes[b] = bytes[b]|bit
                    
                    # Store this byte of data.
                    if line_b:
                        line_b += ","
                    byte = str(hex(bytes[b]))[2:]
                    if len(byte) == 1:
                        byte = "0" + byte
                    line_b += "$" + byte
                
                # Add these four bytes to the whole line.
                line += line_b
            # Got a whole line of 32 bytes, so save it to file.
            export_file.write(".db " + line + "\n")
        export_file.close()
        
        # Show the outcome on the status bar.
        gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
        gtk_thing.statusbar.push(gtk_thing.statusbar_context, "Successfully exported the tiles to '" + file_name + "'.")
        
        return






###############################################################
###############################################################
# 
# Sets up all the GTK stuff so we have a nice friendly GUI.
# 
###############################################################
###############################################################
class setup_the_gtk_stuff:
    def __init__(self):
        # Load the GUI stuff.
        self.xml = gtk.glade.XML('tilemap_editor_gui.glade')
        self.window = self.xml.get_widget("window_main")
        self.window_export_tilemap = self.xml.get_widget("window_export_tilemap")
        self.window_export_tilemap_file_chooser = self.xml.get_widget("filechooserdialog_export_tilemap")
        self.window_import_tilemap = self.xml.get_widget("filechooserdialog_import_tilemap")
        self.window_export_tiles_file_chooser = self.xml.get_widget("filechooserdialog_export_tiles")
        self.window_import_tiles_file_chooser = self.xml.get_widget("filechooserdialog_import_tiles")
        self.window_import_tiles_confirm = self.xml.get_widget("dialog_import_files_confirm")
        self.window_confirm_new_tilemap = self.xml.get_widget("dialog_tilemap_changed")
        self.window_resize_tilemap = self.xml.get_widget("window_resize_tilemap")
        self.window_resize_tilemap_confirm = self.xml.get_widget("dialog_resize_tilemap_confirm")
        self.window_set_palette = self.xml.get_widget("window_set_palette")
        self.window_about = self.xml.get_widget("window_about")
        self.window_import_image_file_chooser = self.xml.get_widget("filechooserdialog_import_image")
        self.area_map = self.xml.get_widget("drawingarea_map")
        self.area_tile = self.xml.get_widget("drawingarea_tiles")
        self.hscrollbar_tilemap = self.xml.get_widget("hscrollbar_tilemap")
        self.vscrollbar_tilemap = self.xml.get_widget("vscrollbar_tilemap")
        self.hbox_tilemap = self.xml.get_widget("hbox2")
        self.label_selected_tile_dec = self.xml.get_widget("label_selected_tile_dec")
        self.label_selected_tile_hex = self.xml.get_widget("label_selected_tile_hex")
        self.label_area_shown_data = self.xml.get_widget("label_area_shown_data")
        self.label_area_total = self.xml.get_widget("label_area_total")
        self.entry_export_tilemap_filename = self.xml.get_widget("entry_export_tilemap_filename")
        self.entry_resize_tilemap_width = self.xml.get_widget("entry_resize_tilemap_width")
        self.entry_resize_tilemap_height = self.xml.get_widget("entry_resize_tilemap_height")
        self.entry_set_palette_tile = self.xml.get_widget("entry_set_palette_tile")
        self.entry_set_palette_sprite = self.xml.get_widget("entry_set_palette_sprite")
        self.image_selected_tile = self.xml.get_widget("image_selected_tile")
        self.optionmenu_zoom = self.xml.get_widget("optionmenu_zoom")
        self.statusbar = self.xml.get_widget("statusbar")
        self.statusbar_context = self.statusbar.get_context_id("statusbar")
        
        # The main drawing area, for displaying the map.
        self.style = self.area_map.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        
        # For the second drawing area - used for showing all available tiles.
        self.style_tile = self.area_tile.get_style()
        self.gc_tile = self.style_tile.fg_gc[gtk.STATE_NORMAL]
        
        # Default size for the hbox container containing the drawing area.
        self.hbox_tilemap_width  = 318
        self.hbox_tilemap_height = 240
        self.show_tilemap_grid   = 0
        
        # Handles the events and methods. Who'd have thunk it?!
        HANDLERS_AND_METHODS = {
            "on_destroy": self.quit,
            "on_menu_file_quit_button_press_event": self.quit,
            "on_menu_file_export_tilemap_activate": self.show_export_tilemap_window,
            "on_menu_file_export_tiles_activate": self.show_export_tiles_window,
            "on_menu_file_new_activate": self.new_tilemap,
            "on_menu_file_import_tiles_activate": self.show_import_tiles_window,
            "on_menu_file_import_tilemap_activate": self.show_import_tilemap_window,
            "on_menu_file_import_image_activate": self.show_import_image_window,
            "on_menu_edit_undo_activate": self.undo_last_action,
            "on_menu_edit_redo_activate": self.redo_last_action,
            "on_menu_edit_map_size_activate": self.resize_tilemap,
            "on_menu_edit_palette_activate": self.palette_button_clicked,
            "on_menu_edit_fill_tiles_activate": tiles.fill_tiles,
            "on_menu_view_zoom_1_activate": self.set_zoom_level_1,
            "on_menu_view_zoom_2_activate": self.set_zoom_level_2,
            "on_menu_view_zoom_4_activate": self.set_zoom_level_4,
            "on_menu_view_show_grid_off_activate": self.tilemap_grid_off,
            "on_menu_view_show_grid_above_activate": self.tilemap_grid_above,
            "on_menu_view_show_grid_below_activate": self.tilemap_grid_below,
            "on_menu_help_about_activate": self.show_about_window,
            "on_hbox_tilemap_size_allocate": self.window_resized,
            "on_button_export_tilemap_cancel_clicked": self.cancel_export_tilemap,
            "on_button_export_tilemap_export_clicked": tilemap.export_data,
            "on_button_export_tilemap_choose_file_clicked": self.export_tilemap_choose_file,
            "on_button_export_tilemap_file_chooser_cancel_clicked": self.export_tilemap_choose_file_cancel,
            "on_button_export_tilemap_file_chooser_ok_clicked": self.export_tilemap_choose_file_ok,
            "on_button_import_tilemap_cancel_clicked": self.import_tilemap_cancel,
            "on_button_import_tilemap_ok_clicked": self.import_tilemap_ok,
            "on_button_import_tilemap_flipped_clicked": self.import_tilemap_flipped,
            "on_button_export_tiles_cancel_clicked": self.export_tiles_cancel,
            "on_button_export_tiles_ok_clicked": self.export_tiles_ok,
            "on_button_import_tiles_cancel_clicked": self.import_tiles_choose_file_cancel,
            "on_button_import_tiles_ok_clicked": self.import_tiles_choose_file_ok,
            "on_button_import_tiles_confirm_cancel_clicked": self.import_tiles_confirm_cancel,
            "on_button_import_tiles_confirm_overwrite_clicked": self.import_tiles_confirm_overwrite,
            "on_button_import_tiles_confirm_append_clicked": self.import_tiles_confirm_append,
            "on_button_import_image_cancel_pressed": self.import_image_cancel,
            "on_button_import_image_normal_clicked": self.import_image_normal,
            "on_button_import_image_bright_clicked": self.import_image_bright,
            "on_button_set_palette_cancel_clicked": self.set_palette_cancel,
            "on_button_set_palette_ok_clicked": self.set_palette_ok,
            "on_tilemap_changed_cancel_clicked": self.tilemap_changed_cancel,
            "on_tilemap_changed_ok_clicked": self.tilemap_changed_ok,
            "on_button_resize_tilemap_cancel_clicked": self.resize_tilemap_cancel,
            "on_button_resize_tilemap_ok_clicked": self.resize_tilemap_ok,
            "on_resize_tilemap_confirm_cancel_clicked": self.resize_tilemap_confirm_cancel,
            "on_resize_tilemap_confirm_ok_clicked": self.resize_tilemap_confirm_ok,
            "on_button_about_close_clicked": self.hide_about_window,
            "on_zoom_1_activate": self.set_zoom_level_1,
            "on_zoom_2_activate": self.set_zoom_level_2,
            "on_zoom_4_activate": self.set_zoom_level_4,
            "on_export_tilemap_bytes_per_line_8_activate": tilemap.set_bytes_per_line_8,
            "on_export_tilemap_bytes_per_line_16_activate": tilemap.set_bytes_per_line_16,
            "on_export_tilemap_bytes_per_line_32_activate": tilemap.set_bytes_per_line_32,
            "on_export_tilemap_bytes_per_line_64_activate": tilemap.set_bytes_per_line_64,
            "on_export_tilemap_bytes_per_line_128_activate": tilemap.set_bytes_per_line_128,
            "on_export_tilemap_bytes_per_line_256_activate": tilemap.set_bytes_per_line_256,
            "on_export_tilemap_bytes_per_line_full_activate": tilemap.set_bytes_per_line_full,
            "on_export_tilemap_data_format_hex_activate": tilemap.set_data_format_hex,
            "on_export_tilemap_data_format_dec_activate": tilemap.set_data_format_dec,
            "on_export_tilemap_data_format_bin_activate": tilemap.set_data_format_bin,
            "on_export_tilemap_include_extra_byte_no_activate": tilemap.set_one_byte_tiles,
            "on_export_tilemap_include_extra_byte_yes_activate": tilemap.set_two_byte_tiles,
            "on_export_tilemap_write_as_bytes_activate": tilemap.set_write_as_bytes,
            "on_export_tilemap_write_as_words_activate": tilemap.set_write_as_words,
            "on_optionmenu_export_tilemap_flip_rotate_no_activate": tilemap.set_flip_rotate_off,
            "on_optionmenu_export_tilemap_flip_rotate_yes_activate": tilemap.set_flip_rotate_on,
            "on_draw_mode_normal_activate": tiles.set_tile_mode_normal,
            "on_draw_mode_x_flipped_activate": tiles.set_tile_mode_x_flip,
            "on_draw_mode_y_flipped_activate": tiles.set_tile_mode_y_flip,
            "on_draw_mode_xy_flipped_activate": tiles.set_tile_mode_xy_flip,
            "on_palette_choose_tile_activate": tiles.set_tile_mode_palette_tile,
            "on_palette_choose_sprite_activate": tiles.set_tile_mode_palette_sprite,
            "on_priority_behind_activate": tiles.set_tile_mode_priority_behind,
            "on_priority_infront_activate": tiles.set_tile_mode_priority_infront,
            "on_hscrollbar_tilemap_value_changed": self.hscrollbar_tilemap_changed,
            "on_vscrollbar_tilemap_value_changed": self.vscrollbar_tilemap_changed
        }        
        self.xml.signal_autoconnect(HANDLERS_AND_METHODS)
        
        # Events for the map's drawing area.
        self.area_map.connect("button_press_event", self.button_press_event)
        self.area_map.connect("expose-event", self.area_map_expose_cb)
        
        # Events for the tile chooser's drawing area.
        self.area_tile.connect("button_press_event", self.area_tile_button_press_event)
        self.area_tile.connect("expose-event", self.area_tile_expose_cb)
        
        # Convert and load the XPMs to pixmaps.
        tiles.xmp_to_pixmaps(self.window.window)
    
    
    
    ###############################################################
    # Gets called when the window is resized, then stores the
    # width and height of the hbox which contains the tilemap
    # drawing area widget.
    ###############################################################
    def window_resized(self, widget, event):
        self.hbox_tilemap_width  = event.width
        self.hbox_tilemap_height = event.height
        
        self.sort_out_tilemap_scrollbars()
        
        return True
    
    
    
    ###############################################################
    # Redraws the map display and prepares for the end of the world.
    ###############################################################
    def area_map_expose_cb(self, area_map, event):
        #self.draw_grid()
        self.draw_map()
        return True
    
    
    
    ###############################################################
    # Redraws the tile display and prepares for the end of the moon.
    ###############################################################
    def area_tile_expose_cb(self, area_tile, event):
        self.fill_tile_viewer()
        return True
    
    
    
    ###############################################################
    # Draws the grid in the background.
    ###############################################################
    def draw_grid(self):
        width, height = self.grid_limits()
        space   = 2**tiles.zoom
        width  *= 8
        height *= 8
        
        # Draw the grid lines.
        for x in range(0, ((width * space) + 1), (8 * space)):
            self.area_map.window.draw_line(self.gc, x, 0, x, (height * space))
        for y in range(0, ((height * space) + 1), (8 * space)):
            self.area_map.window.draw_line(self.gc, 0, y, (width * space), y)
        return
    
    
    
    ###############################################################
    # Draws the list of blocks in "self.blocks".
    ###############################################################
    def draw_map(self):
        multi  = 2**tiles.zoom
        spaced = (2**tiles.zoom) * 8
        width, height = self.grid_limits()
        
        # Show grid below tiles?
        if self.show_tilemap_grid == 2:
            self.draw_grid()
            
        for x in range(tilemap.start[0], (tilemap.start[0] + (width * multi))):
            for y in range(tilemap.start[1], (tilemap.start[1] + (height * multi))):
                try:
                    self.draw_pixmap(((x - tilemap.start[0]) * spaced), ((y - tilemap.start[1]) * spaced), tilemap.world[x][y][0])
                except:
                    print "#####"
                    print "self.draw_pixmap(((" + str(x) + " - " + str(tilemap.start[0]) + ") * " + str(spaced) + "), ((" + str(y) + " - " + str(tilemap.start[1]) + ") * " + str(spaced) + "), tilemap.world[x][y][0]"
                    print "#####"
        
        # Show grid above tiles?
        if self.show_tilemap_grid == 1:
            self.draw_grid()
        
        return
    
    
    
    ###############################################################
    # Returns the maximum size of the draw area.
    ###############################################################
    def grid_limits(self):
        width  = 32
        height = 24
        max_width  = (self.hbox_tilemap_width / 8)
        max_height = (self.hbox_tilemap_height / 8)
        
        if tilemap.width < max_width:
            width = tilemap.width
        else:
            width = max_width
        if tilemap.height < max_height:
            height = tilemap.height
        else:
            height = max_height
        
        # Take into account the zoom level.
        space = 2**tiles.zoom
        return (width / space), (height / space)
    
    
    
    ###############################################################
    # Makes changes based on the scrollbars.
    ###############################################################
    def sort_out_tilemap_scrollbars(self):
        h_adjustment = self.hscrollbar_tilemap.get_adjustment()
        v_adjustment = self.vscrollbar_tilemap.get_adjustment()
        
        if tiles.zoom == 2:
            add_x = (tilemap.width / 2) + (tilemap.width / 4)
            add_y = (tilemap.height / 2) + (tilemap.height / 4)
        elif tiles.zoom == 1:
            add_x = (tilemap.width / 2)
            add_y = (tilemap.height / 2)
        else:
            add_x = 0
            add_y = 0
        
        
        space = 2**tiles.zoom
        
        # Is part of the tilemap off-screen (width)?
        if (self.hbox_tilemap_width / 8) < (tilemap.width * space):
            h_adjustment.upper = 32 + (tilemap.width - (self.hbox_tilemap_width / 8)) + add_x
        else:
            h_adjustment.upper = 32
        
        # Is part of the tilemap off-screen (height)?
        if (self.hbox_tilemap_height / 8) < (tilemap.height * space):
            v_adjustment.upper = 24 + (tilemap.height - (self.hbox_tilemap_height / 8)) + add_y
        else:
            v_adjustment.upper = 24
        
        #print h_adjustment.upper
        #print v_adjustment.upper
        
        return
    
    
    
    # Resets the scrollbars.
    def reset_tilemap_scrollbars(self):
        h_adjustment = self.hscrollbar_tilemap.get_adjustment()
        v_adjustment = self.vscrollbar_tilemap.get_adjustment()
        h_adjustment.value = 0
        v_adjustment.value = 0
        return
    
    
    
    ###############################################################
    # Handles what happens when the a mouse button is pressed on
    # the tilemap.
    ###############################################################
    def button_press_event(self, widget, event):
        # Left mouse button?
        if event.button == 1:
            space  = 2**tiles.zoom
            spaced = 8 * space
            width, height = self.grid_limits()
            width  *= (8 * space)
            height *= (8 * space)
            
            # Align it to the grid.
            x = int(event.x / spaced)
            y = int(event.y / spaced)
                        
            # Check if they clicked outside of the grid.
            if ((x * spaced) > ((width * space) - spaced)) or ((y * spaced) > ((height * space) - spaced)):
                return True
            
            # Save the current tile to the undo list.
            tilemap.undo_list.append([[x], [y], [deepcopy(tilemap.world[(x + tilemap.start[0])][(y + tilemap.start[1])])]])
            
            # Draw the block and save it.
            tilemap.world[(x + tilemap.start[0])][(y + tilemap.start[1])][0] = tiles.selected_tile
            tilemap.world[(x + tilemap.start[0])][(y + tilemap.start[1])][1] = tiles.mode
            self.draw_pixmap((x * spaced), (y * spaced), tiles.selected_tile)
            tilemap.changed = 1
            #print tilemap.world
        return True
    
    
    
    ###############################################################
    # Handles what happens when the a mouse button is pressed on
    # the tile chooser.
    ###############################################################
    def area_tile_button_press_event(self, widget, event):
        # Left mouse button?
        if event.button == 1:
            if event.x > 176:
                return True
            
            # Find which tile was clicked on.
            x = int(event.x / 8)
            y = int(event.y / 8)
            tiles.set_selected_tile(x + (y * 22))   # 22 tiles per row.
        return True
    
    
    
    ###############################################################
    # Draws a pixmap to the block in "x" and "y".
    ###############################################################
    def draw_pixmap(self, x, y, tile):
        #print str(x) + ", " + str(y) + " = " + str(tile)
        try:
            tile = tiles.pixmap_tiles[tiles.zoom][tile]
        except:
            print "ERROR:: " + str(x) + ", " + str(y) + " = " + str(tile)
            tile = tiles.pixmap_tiles[tiles.zoom][0]
        self.area_map.window.draw_drawable(self.gc, tile, 0, 0, x, y, -1, -1)
        return
    
    
    
    ###############################################################
    # This function takes a trip to Alaska and clubs seals.
    ###############################################################
    def update_label_area_shown_data(self):
        width, height = self.grid_limits()
        space  = 2**tiles.zoom
        width  = (width * space) - 1
        height = (height * space) - 1
        #width  -= 1
        #height -= 1
        self.label_area_shown_data.set_text(str(tilemap.start[0]) + "," + str(tilemap.start[1]) + " to " + str(tilemap.start[0] + width) + "," + str(tilemap.start[1] + height))
        return
    
    
    
    ###############################################################
    # This function drives a steam-roller to work.
    ###############################################################
    def update_label_area_total(self):
        self.label_area_total.set_text("(total size: " + str(tilemap.width) + "x" + str(tilemap.height) + ")")
        return
    
    
    
    ###############################################################
    # Fills the tile-viewer with all tiles we have for the user to
    # choose. This drawing area can display a 22x24 grid of them.
    ###############################################################
    def fill_tile_viewer(self):
        y = 0
        c = 0
        for i in range(0, len(tiles.pixmap_tiles[0])):
            self.area_tile.window.draw_drawable(self.gc_tile, tiles.pixmap_tiles[0][i], 0, 0, (c * 8), y, 8, 8)
            c += 1
            if c == 22:
                y += 8
                c = 0
        return
    
    
    
    ###############################################################
    # Changes the zoom level.
    ###############################################################
    def set_zoom_level_1(self, object, event = 0):
        self.change_zoom_level(0)
        return True
    def set_zoom_level_2(self, object, event = 0):
        self.change_zoom_level(1)
        return True
    def set_zoom_level_4(self, object, event = 0):
        self.change_zoom_level(2)
        return True
    
    def change_zoom_level(self, level):
        tiles.zoom = level
        
        # SUPERFLUOUS!
        # Increase the drawing area widget's size.
        #multiplier = 2**level
        #self.area_map.size_allocate((15, 39, ((tilemap.width * 8) * multiplier), ((tilemap.height * 8) * multiplier)))
        
        # Reposition the map to show the top-left position.
        tilemap.start[0] = 0
        tilemap.start[1] = 0
        
        # Reset the scrollbars.
        self.reset_tilemap_scrollbars()
        
        # Sort out the scroll bars and resize the display.
        self.sort_out_tilemap_scrollbars()
        self.update_label_area_shown_data()
        
        # Update the display. Do this last.
        self.area_map.window.clear()
        self.area_map_expose_cb(0, 0)
        return
    
    
    
    ###############################################################
    # Undos the last tile placing.
    ###############################################################
    def undo_last_action(self, object, event = 0):
        # Anything to undo?
        if not len(tilemap.undo_list):
            print "Nothing to undo."
            return True
        
        # Find the last placed tile and stuff.
        x      = int(str(tilemap.undo_list[(len(tilemap.undo_list) - 1)][0])[1:][:-1])
        y      = int(str(tilemap.undo_list[(len(tilemap.undo_list) - 1)][1])[1:][:-1])
        try:
            tile_a = tilemap.undo_list[(len(tilemap.undo_list) - 1)][2][0][0]
            tile_b = tilemap.undo_list[(len(tilemap.undo_list) - 1)][2][0][1]
            tile   = [tile_a, tile_b]
        except:
            tile = tilemap.undo_list[(len(tilemap.undo_list) - 1)][2]
        
        # Check if the location is still accessable. A resizing may have
        # made the location out of bounds.
        if x >= tilemap.width or y >= tilemap.height:
            print "That tile is out of bounds. This can occur when the tilemap has been shrunk after placing tiles in an area which no-longer exists."
            self.fix_out_of_bounds_un_re_does()
            self.fix_out_of_bounds_un_re_does()
            print "Redo and undo lists cleared of all items which are out of bounds."
            return True
        
        # Add it to the redo list.
        redo = [[x], [y]]
        redo.append(deepcopy(tilemap.world[x][y]))
        tilemap.redo_list.append(deepcopy(redo))
        
        # Perform the undo, removing it from the list.
        tilemap.world[x][y] = tile
        tilemap.undo_list.pop()
        
        # Update the display. Do this last.
        self.area_map.window.clear()
        self.area_map_expose_cb(0, 0)
        
        return True
    
    
    
    ###############################################################
    # Redoes the last tile placing.
    ###############################################################
    def redo_last_action(self, object, event = 0):
        # Anything to redo?
        if not len(tilemap.redo_list):
            print "Nothing to redo."
            return True
        
        # Find the last placed tile and stuff.
        x    = int(str(tilemap.redo_list[(len(tilemap.redo_list) - 1)][0])[1:][:-1])
        y    = int(str(tilemap.redo_list[(len(tilemap.redo_list) - 1)][1])[1:][:-1])
        tile = tilemap.redo_list[(len(tilemap.redo_list) - 1)][2]
        
        # Check if the location is still accessable. A resizing may have
        # made the location out of bounds.
        if x >= tilemap.width or y >= tilemap.height:
            print "That tile is out of bounds. This can occur when the tilemap has been shrunk after placing tiles in an area which no-longer exists."
            self.fix_out_of_bounds_un_re_does()
            self.fix_out_of_bounds_un_re_does()
            print "Redo and undo lists cleared of all items which are out of bounds."
            return True
        
        # Add it to the redo list.
        undo = [[x], [y]]
        undo.append(deepcopy(tilemap.world[x][y]))
        tilemap.undo_list.append(deepcopy(undo))
        
        # Perform the undo, removing it from the list.
        tilemap.world[x][y] = tile
        tilemap.redo_list.pop()
        
        # Update the display. Do this last.
        self.area_map.window.clear()
        self.area_map_expose_cb(0, 0)
        
        return True
    
    
    
    ###############################################################
    # Removes all items from the undo and redo lists which refer
    # to tiles whic are no-longer in bounds of the current tilemap.
    ###############################################################
    def fix_out_of_bounds_un_re_does(self):
        # Fix the undo list.
        for i in range(0, len(tilemap.undo_list)):
            # Some items are popped from the list, so this might fail because the
            # range/loop doesn't get updated...
            try:
                if int(str(tilemap.undo_list[i][0])[1:][:-1]) >= tilemap.width or int(str(tilemap.undo_list[i][1])[1:][:-1]) >= tilemap.height:
                    tilemap.undo_list.pop(i)
                    i -= 1
            except:
                break
        
        # Fix the redo list.
        for i in range(0, len(tilemap.redo_list)):
            try:
                if int(str(tilemap.redo_list[i][0])[1:][:-1]) >= tilemap.width or int(str(tilemap.redo_list[i][1])[1:][:-1]) >= tilemap.height:
                    tilemap.redo_list.pop(i)
                    i -= 1
            except:
                break
        
        return
    
    
    
    ###############################################################
    # Show the window allowing the user to import a tilemap.
    ###############################################################
    def show_import_tilemap_window(self, object, event = 0):
        self.window_import_tilemap.show()
        return True
    
    # Cancels the importing of the tilemap.
    def import_tilemap_cancel(self, object, event = 0):
        self.window_import_tilemap.hide()
        return True
    
    # Imports the tilemap.
    def import_tilemap_ok(self, object, event = 0, flip_rotate = 0):
        self.statusbar.pop(self.statusbar_context)
        if tilemap.import_tilemap(self.window_import_tilemap.get_filename(), flip_rotate) == True:
            self.area_map_expose_cb(0, 0)
            self.statusbar.push(self.statusbar_context, "Successfully loaded tilemap from '" + self.window_import_tilemap.get_filename() + "'.")
            self.update_label_area_shown_data()
            self.update_label_area_total()
        else:
            self.statusbar.push(self.statusbar_context, "ERROR:: Could not load tilemap from '" + self.window_import_tilemap.get_filename() + "'.")
        self.window_import_tilemap.hide()
        
        return True
    
    # Imports the tilemap, but rotates it anti-clockwise.
    def import_tilemap_flipped(self, object, event = 0):
        self.import_tilemap_ok(0, 0, 1)
        return True
    
    
    
    
    ###############################################################
    # Shows the "Export Tilemap" window which allows users to
    # export the tilemap.
    ###############################################################
    def show_export_tilemap_window(self, object, event = 0):
        self.window_export_tilemap.show()
        return True
    
    # Hides and resets the "Export Tilemap" window.
    def cancel_export_tilemap(self, object, event = 0):
        self.window_export_tilemap.hide()
        return True
    
    # Show the file chooser window allowing the user to choose the name of
    # the file to export to.
    def export_tilemap_choose_file(self, object, event = 0):
        self.window_export_tilemap_file_chooser.show()
        return True
    
    # Handles the "Cancel" button on the "Export Tilemap" file chooser.
    def export_tilemap_choose_file_cancel(self, object, event = 0):
        self.window_export_tilemap_file_chooser.hide()
        return True
    
    # Handles the "OK" button on the "Export Tilemap" file chooser.
    def export_tilemap_choose_file_ok(self, object, event = 0):
        self.window_export_tilemap_file_chooser.hide()
        self.entry_export_tilemap_filename.set_text(self.window_export_tilemap_file_chooser.get_filename())
        return True
    
    
    
    ###############################################################
    # Shows the "Export Tiles" window which allows users to export
    # the tiles.
    ###############################################################
    def show_export_tiles_window(self, object, event = 0):
        self.window_export_tiles_file_chooser.show()
        return True
    
    # Handles the "Cancel" button on the "Export Tiles" window.
    def export_tiles_cancel(self, object, event = 0):
        self.window_export_tiles_file_chooser.hide()
        return True
    
    # Handles the "Save As" button on the "Export Tiles" window.
    def export_tiles_ok(self, object, event = 0):
        tiles.export_tiles(self.window_export_tiles_file_chooser.get_filename())
        self.window_export_tiles_file_chooser.hide()
        return True
    
    
    
    ###############################################################
    # Shows the "Import Image" window, allowing them to choose an
    # image to import.
    ###############################################################
    def show_import_image_window(self, object, event = 0):
        self.window_import_image_file_chooser.show()
        return True
    
    # Handles the "Cancel" button on the "Import Image" file chooser dialog.
    def import_image_cancel(self, object, event = 0):
        self.window_import_image_file_chooser.hide()
        return True
    
    
    # Handles the "Import Normal" button on the "Import Image" file chooser dialog.
    def import_image_normal(self, object, event = 0):
        import_an_image.setup_class(self.window_import_image_file_chooser.get_filename(), 0)
        import_an_image.load_and_convert()
        import_an_image.all_done_mon_capitan()
        self.window_import_image_file_chooser.hide()
        return True
    
    
    # Handles the "Import Bright" button on the "Import Image" file chooser dialog.
    def import_image_bright(self, object, event = 0):
        import_an_image.setup_class(self.window_import_image_file_chooser.get_filename(), 1)
        import_an_image.load_and_convert()
        import_an_image.all_done_mon_capitan()
        self.window_import_image_file_chooser.hide()
        return True
    
    
    
    ###############################################################
    # Creates a blank tilemap.
    ###############################################################
    def new_tilemap(self, object, event = 0):
        if tilemap.changed:
            self.window_confirm_new_tilemap.show()
        else:
            tilemap.new()
        
        # Clearn redo/undo history.
        tilemap.undo_list = []
        tilemap.redo_list = []
        
        return True
    
    # They cancelled the creation of a new tilemap.
    def tilemap_changed_cancel(self, object, event = 0):
        self.window_confirm_new_tilemap.hide()
        return True
    
    # They cancelled the creation of a new tilemap.
    def tilemap_changed_ok(self, object, event = 0):
        self.window_confirm_new_tilemap.hide()
        tilemap.new()
        return True
    
    
    
    ###############################################################
    # Give them the window allowing them to change the size of the
    # tilemap.
    ###############################################################
    def resize_tilemap(self, object, event = 0):
        self.entry_resize_tilemap_width.set_text(str(tilemap.width))
        self.entry_resize_tilemap_height.set_text(str(tilemap.height))
        self.window_resize_tilemap.show()
        return True
    
    # Cancel the tilemap resizing.
    def resize_tilemap_cancel(self, object, event = 0):
        self.window_resize_tilemap.hide()
        return True
    
    # Accept and check the new size for the tile map, then implement it.
    def resize_tilemap_ok(self, object, event = 0):
        # Check that the new size is not smaller. If it is, warn the user.
        if int(self.entry_resize_tilemap_width.get_text()) < tilemap.width or int(self.entry_resize_tilemap_height.get_text()) < tilemap.height:
            self.window_resize_tilemap_confirm.show()
        else:
            tilemap.resize_tilemap()
            self.window_resize_tilemap.hide()
        return True
    
    # Cancel the tilemap resizing.
    def resize_tilemap_confirm_cancel(self, object, event = 0):
        self.window_resize_tilemap_confirm.hide()
        self.window_resize_tilemap.hide()
        return True
    
    # Confirm the tilemap resizing.
    def resize_tilemap_confirm_ok(self, object, event = 0):
        tilemap.resize_tilemap()
        self.window_resize_tilemap_confirm.hide()
        self.window_resize_tilemap.hide()
        return True
    
    
    
    ###############################################################
    # Brings up the palette setting window.
    ###############################################################
    def palette_button_clicked(self, object, event = 0):
        self.window_set_palette.show()
        return True
    
    # Cancels the updating of the palette.
    def set_palette_cancel(self, object, event = 0):
        self.window_set_palette.hide()
        return True
    
    # Accepts the new palette data.
    def set_palette_ok(self, object, event = 0):
        palette.set_palette()
        return True
    
    
    
    ###############################################################
    # Brings up the "About" window.
    ###############################################################
    def show_about_window(self, object, event = 0):
        self.window_about.show()
        return True
    
    # Cancels the updating of the palette.
    def hide_about_window(self, object, event = 0):
        self.window_about.hide()
        return True
    
    
    
    ###############################################################
    # Enables or disables the showing of the grid-lines on the
    # tilemap.
    ###############################################################
    def tilemap_grid_off(self, object, event = 0):
        self.show_tilemap_grid = 0
        self.draw_map()
        return True
    
    # Enables the grid-lines - shows them above the tiles.
    def tilemap_grid_above(self, object, event = 0):
        self.show_tilemap_grid = 1
        self.draw_map()
        return True
    
    # Enables the grid-lines - shows them below the tiles.
    def tilemap_grid_below(self, object, event = 0):
        self.show_tilemap_grid = 2
        self.draw_map()
        return True
    
    
    
    ###############################################################
    # Shows the "Open File" dialog allowing users to choose a
    # file containing tiles to import.
    ###############################################################
    def show_import_tiles_window(self, object, event = 0):
        self.window_import_tiles_file_chooser.show()
        return True
    
    # Cancel importing of tiles.
    def import_tiles_choose_file_cancel(self, object, event = 0):
        self.window_import_tiles_file_chooser.hide()
        return True
    
    # They have chosen a file containing the tiles.
    def import_tiles_choose_file_ok(self, object, event = 0):
        if len(tiles.xpm_tiles[0]) > 1:
            self.window_import_tiles_confirm.show()
        else:
            self.import_tiles(self.window_import_tiles_file_chooser.get_filename(), 1)
        return True
    
    # Cancel importing of tiles.
    def import_tiles_confirm_cancel(self, object, event = 0):
        self.window_import_tiles_confirm.hide()
        self.window_import_tiles_file_chooser.hide()
        return True
    
    # Overwrite current tiles.
    def import_tiles_confirm_overwrite(self, object, event = 0):
        self.import_tiles(self.window_import_tiles_file_chooser.get_filename(), 1)
        return True
    
    # Add the new tiles to the end of the currently existing tiles.
    def import_tiles_confirm_append(self, object, event = 0):
        self.import_tiles(self.window_import_tiles_file_chooser.get_filename(), 0)
        return True
        
    # "source_file" == file to load. "overwrite" == 0 for append and 1 for overwrite.
    def import_tiles(self, source_file, overwrite):
        self.window_import_tiles_confirm.hide()
        self.window_import_tiles_file_chooser.hide()
        
        if overwrite:
            return_value = tiles.load_tiles_and_overwrite(self.window_import_tiles_file_chooser.get_filename())
        else:
            return_value = tiles.load_tiles_and_make_xpms(self.window_import_tiles_file_chooser.get_filename())
        
        # Did it work?
        if return_value != True:
            self.statusbar.pop(self.statusbar_context)
            self.statusbar.push(self.statusbar_context, "ERROR:: Could not load file from '" + source_file + "'.")
            return False
        
        # It worked.
        tiles.xmp_to_pixmaps(self.window.window)
        self.area_map_expose_cb(0, 0)
        self.area_tile_expose_cb(0, 0)
        tiles.set_selected_tile(0)
        self.statusbar.pop(self.statusbar_context)
        self.statusbar.push(self.statusbar_context, "Successfully loaded " + str(len(tiles.xpm_tiles[0])) + " tiles from '" + source_file + "'.")
        return True
    
    
    
    ###############################################################
    # Handles the scroll bar events.
    ###############################################################
    # Scrolls the tilemap horizontally.
    def hscrollbar_tilemap_changed(self, object, event = 0):
        h_adjustment = self.hscrollbar_tilemap.get_adjustment()
        tilemap.start[0] = int(h_adjustment.value)
        self.update_label_area_shown_data()
        self.draw_map()
        return True
    
    # Scrolls the tilemap vertically.
    def vscrollbar_tilemap_changed(self, object, event = 0):
        v_adjustment = self.vscrollbar_tilemap.get_adjustment()
        tilemap.start[1] = int(v_adjustment.value)
        self.update_label_area_shown_data()
        self.draw_map()
        return True
    
    
    
    ###############################################################
    # Handles "quit" events.
    ###############################################################
    def quit(self, object, event = 0):
        gtk.main_quit()
        return True






###############################################################
###############################################################
###############################################################
# 
# Start of global code.
#
###############################################################



###############################################################
# El main.
###############################################################
def main():
    gtk_thing.statusbar.pop(gtk_thing.statusbar_context)
    gtk_thing.statusbar.push(gtk_thing.statusbar_context, "Loaded successfully.")
    gtk.main()
    return 0



###############################################################
###############################################################
# 
# Execution starts here.
# 
###############################################################
###############################################################
if __name__ == "__main__":
    # Create some tiles to use.
    palette = palettes_and_colours()
    tiles = create_tiles()
    #tiles.load_tiles_and_make_xpms("tile_data_chars.inc")
    
    # Setup the map.
    tilemap = tilemap_things_and_such()
    import_an_image = image_import()
    
    # Start some GTK goodness.
    gtk_thing = setup_the_gtk_stuff()
    
    tiles.set_selected_tile(0)
    tilemap.new()
    
    #import_an_image.load_and_convert()
    ##import_an_image.update_and_show_image()   0,2,48,8,42,21,63,12,3,56,1,32,4,15,31,43
    #import_an_image.all_done_mon_capitan()
    main()
