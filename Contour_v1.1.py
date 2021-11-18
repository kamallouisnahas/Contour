#MODULES############################################################################################################################

import os
import sys
import shutil
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import multiprocessing
import numpy as np
import tifffile
import time
import threading
import math
import cProfile
import io
import pstats
import operator
import copy
import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import csv
import random
import statistics
from scipy.spatial import ConvexHull
from scipy.ndimage import gaussian_filter
import logging
import psutil
import gc


def profile(func):
    '''A decorator that uses cProfile to profile a function'''

    def inner(*args, **kwargs):
        profile=cProfile.Profile()
        profile.enable()
        ret_val=func(*args,**kwargs)
        profile.disable()
        s=io.StringIO()
        sortby='cumulative'
        ps=pstats.Stats(profile,stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return ret_val
    
    return inner

def usage():
    # gives a single float value
    cpu=psutil.cpu_percent()
    # gives an object with many fields
    psutil.virtual_memory()
    # you can convert that object to a dictionary 
    dict(psutil.virtual_memory()._asdict())
    # you can have the percentage of used RAM
    ram=psutil.virtual_memory().percent
    # you can calculate percentage of available memory
    available=psutil.virtual_memory().available * 100 / psutil.virtual_memory().total
    print('CPU:',cpu,'RAM:',ram,'AVAILABLE:',available)

usage()





#CLASSES############################################################################################################################
class Files(object):
    
    def change_or_make_directory(*foldernames,parent_directory=True):
        subdirectories=len(foldernames)
        folder_level=0
        if parent_directory: #if start at the parent directory
            os.chdir(directory_name)
        while folder_level<subdirectories:
            if not os.path.isdir(foldernames[folder_level]):
                os.mkdir(foldernames[folder_level])
            os.chdir(foldernames[folder_level])
            folder_level+=1
    
    def change_and_check_directory(*foldernames,parent_directory=True):
        subdirectories=len(foldernames)
        folder_level=0
        if parent_directory: #if start at the parent directory
            os.chdir(directory_name)
        while folder_level<subdirectories:
            if not os.path.isdir(foldernames[folder_level]):
                errormessage='Error: folder has been moved or deleted. \n\nThe folder '+str(foldernames[folder_level])+' could not be located.'
                messagebox.showwarning('Folder missing',errormessage)
            os.chdir(foldernames[folder_level])
            folder_level+=1
    
    def change_and_overwrite_directory(*foldernames,parent_directory=True):
        subdirectories=len(foldernames)
        folder_level=0
        if parent_directory: #if start at the parent directory
            os.chdir(directory_name)
        while folder_level<subdirectories:
            if os.path.isdir(foldernames[folder_level]):
                shutil.rmtree((foldernames[folder_level]))
            os.mkdir(foldernames[folder_level])
            os.chdir(foldernames[folder_level])
            folder_level+=1


class Window(Frame): #Window class is used to display the source_image_stack

    scroll_bar_height=35
    max_dimensions=512
    square_dimensions=0
    original_width=''
    original_height=''
    scale_factor=1

    def __init__(self,filename,master=None): #master denotes the Tkinter window
        Frame.__init__(self,master) #Image module does not work without Frame superclass
        self.master=master
        self.filename=filename
        self.__version=1
        global load_image
        load_image=Image.open(filename) #import the image
    
    def rescale_stack(self):
        if len(stack)>0:
            array=stack[0].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
            global source_image_width
            global source_image_height
            global scale_factor
            source_image_width=Window.square_dimensions
            source_image_height=Window.square_dimensions
            

            scale_factor=0
            if source_image_width>Window.max_dimensions or source_image_height>Window.max_dimensions:     
                valid_size=False
                while valid_size==False:
                    #downscale by factor of 2 each iteration
                    scale_factor+=2
                    source_image_width=int(round(source_image_width/2,0))
                    source_image_height=int(round(source_image_height/2,0))
                    for z in range(0,len(stack)):
                        current_array=stack[z].image_array
                        current_array=current_array[0::2]
                        current_array=np.rot90(current_array,k=1)
                        current_array=current_array[0::2]
                        current_array=np.rot90(current_array,k=-1)
                        stack[z].image_array=current_array
                        gc.collect()
                    
                    if source_image_width>Window.max_dimensions or source_image_height>Window.max_dimensions:
                        valid_size=False
                    else:
                        valid_size=True
                Window.scale_factor=scale_factor
                global message_template
                message_template='''
The image(s) have been scaled down by a factor of {0} because the dimensions are too large. This rescaling will improve the efficiency of the program.
            
Original dimensions: {1} x {2}
New dimensions: {3} x {4}

The scale factor will be automatically accounted for during quantitation of segmented volumes.

The Z depth has not been scaled down. If you view your segmented volume in 3D (e.g. using 3D Viewer in Fiji), ensure you reduce the voxel depth by a factor of {0}.
'''
                message_template=message_template.format(scale_factor,Window.original_width,Window.original_height,source_image_width,source_image_height)
                complete_message=message_template+'\nThis information can be retrieved from the log file.'
                messagebox.showinfo(title='Image(s) have been scaled down',message=complete_message)


    def ensure_stack_is_square(self):
        if source_image_width!=source_image_height:
            difference=abs(source_image_width-source_image_height)
            
            half_width=difference/2
            
            if difference % 2 == 0:
                even=True
            else:
                even=False
            
            half_width=math.floor(half_width)
            if source_image_width>source_image_height:
                for z in range(0,len(stack)):
                    current_array=stack[z].image_array
                    if even:
                        left_bar=np.zeros((source_image_width,half_width))
                    elif not even:
                        left_bar=np.zeros((source_image_width,half_width+1))
                    right_bar=np.zeros((source_image_width,half_width))
                    left_bar=np.where(left_bar==0,-1,left_bar)
                    right_bar=np.where(right_bar==0,-1,right_bar)
                    combined_array=np.concatenate((left_bar,current_array,right_bar),axis=1)
                    stack[z].image_array=combined_array
                Window.square_dimensions=source_image_width

            elif source_image_width<source_image_height:
                for z in range(0,len(stack)):
                    current_array=stack[z].image_array
                    if even:
                        lower_bar=np.zeros((half_width,source_image_height))
                    elif not even:
                        lower_bar=np.zeros((half_width+1,source_image_height))
                    upper_bar=np.zeros((half_width,source_image_height))
                    lower_bar=np.where(lower_bar==0,-1,lower_bar)
                    upper_bar=np.where(upper_bar==0,-1,upper_bar)
                    combined_array=np.concatenate((upper_bar,current_array,lower_bar),axis=0)
                    stack[z].image_array=combined_array
                Window.square_dimensions=source_image_height
        else:
            Window.square_dimensions=source_image_width
            
    def process_image(self):
        global stack
        global source_image_width
        global source_image_height
        stack=[]

        positive_infinity=float('inf')
        i=0
        while i < positive_infinity:
            try:
                load_image.seek(i) #work through image planes in the 3d stack
                next_array=np.array(load_image,dtype="uint8") #load as unsigned integers of 8 bit (0 - 255 without + or - signs)
                array_object=PixelArray(next_array) #additional data stored in object form, such as version number
                stack.append(array_object) #append each image plane to the stack [] list
                i=i+1
            except EOFError: #break when reach the end of the file
                break
        
        array=stack[0].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
        new_image=Image.fromarray(array)
        dimensions=array.astype(np.double)
        Window.original_width=dimensions.shape[0]
        Window.original_height=dimensions.shape[1]
        source_image_width=dimensions.shape[0]
        source_image_height=dimensions.shape[1]

        self.ensure_stack_is_square()
        self.rescale_stack()

        
        
        middle_slice=len(stack)/2
        global current_z
        global current_z_left
        current_z=int(middle_slice) #must convert into integer to use for indexing
        current_z_left=current_z
    
    
    def display_image(self,z_slice):
        global source_image_width
        global source_image_height
        global source_image_canvas
        array=stack[z_slice].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
        new_image=Image.fromarray(array)
        dimensions=array.astype(np.double)
        source_image_width=dimensions.shape[0]
        source_image_height=dimensions.shape[1]
        render=ImageTk.PhotoImage(new_image)
        img=Label(self,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
        img.image=render #.image is a method attribute of Label
        source_image_canvas=Canvas(self.master,width=source_image_width,height=source_image_height)
        source_image_canvas.grid(row=2,column=1,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
        source_image_canvas.create_image(source_image_width/2,source_image_height/2,image=render)



    
    def display_scroll_bar(self,initial=False):
        global left_scroll_bar
        left_scroll_bar=Canvas(self.master,width=source_image_width,height=Window.scroll_bar_height,bg='lightsteelblue')

        left_scroll_bar.grid(row=3,column=1,columnspan=9,padx=5,pady=2.5,sticky=N+S+E+W)

        toggle_half_width=int(source_image_width/len(stack))

        if initial==True:
            left_scroll_bar.create_rectangle(source_image_width/2-toggle_half_width,0,(source_image_width/2)+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue')
            left_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(int(current_z)))

        def scroll_slice(event):
            global conversion_ratio
            if event.x>=1 and event.x<=source_image_width:
                conversion_ratio=len(stack)/source_image_width
                current_z=int(event.x*conversion_ratio)
                return current_z
            return None

        
        def move_z_cursor(event):
            nonlocal toggle_half_width
            global current_z
            global current_z_left
            current_z=scroll_slice(event)
            current_z_left=current_z
            if current_z!=None and current_z!=0 and current_z<=len(stack):
                

                left_scroll_bar.delete('all')
                left_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                left_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))

                if LockPreview.lock_previews:
                    right_scroll_bar.delete('all')
                    right_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                    right_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))   


            left_scroll_bar.bind('<B1-Motion>',scroll_source_image_stack)
            bind_collect_pixels()
        
        def scroll_source_image_stack(event):
            current_z=scroll_slice(event)
            if isinstance(current_z,int):
                if current_z>0:
                    self.display_image(current_z-1)

                    if LockPreview.lock_previews:
                        preview.display_image(current_z-1)
                        if SegmentedArray.preview_option:
                            PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                            PreviewWindow.preview_array.view_preview()


            left_scroll_bar.bind('<B1-Motion>',move_z_cursor)
            bind_collect_pixels()

        left_scroll_bar.bind('<B1-Motion>',move_z_cursor)
        bind_collect_pixels()
        
    def display_stack_extremes(self,master=None):
        first_slice_label=Label(master,text='1')
        first_slice_label.grid(row=3,column=0,padx=2,pady=2,sticky=E)
        last_slice=str(len(stack))
        last_slice_label=Label(master,text=last_slice)
        last_slice_label.grid(row=3,column=10,padx=2,pady=2,sticky=W)

class StringZ(object):

    @staticmethod
    def int_to_3_dec_string(z_index):
        if z_index<10:
            string_z_pos='00'+str(z_index)
        elif z_index<100:
            string_z_pos='0'+str(z_index)
        else:
            string_z_pos=str(z_index)
        assert int(string_z_pos)==int(z_index)
        return string_z_pos

class PreviewWindow(Window):

    preview_array=None
    right_preview=None

    @staticmethod
    def enable_preview_button():
        if PreviewWindow.preview_array==None:
            PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
        PreviewWindow.preview_array.enable_preview()

    def __init__(self,filename,master):
        super().__init__(filename=filename,master=master)
        self.__version=1
    
    def process_image(self):
        global preview_stack
        preview_stack=[]

        positive_infinity=float('inf') #imported images are of unlimited stack size
        i=0
        while i < positive_infinity:
            try:
                load_image.seek(i) #work through image planes in the 3d stack
                next_array=np.array(load_image,dtype="uint8") #load as unsigned integers of 8 bit (0 - 255 without + or - signs)
                array_object=PixelArray(next_array) #additional data stored in object form, such as version number
                stack.append(array_object) #append each image plane to the stack [] list
                i=i+1
            except EOFError: #break when reach the end of the file
                break
        
        middle_slice=len(stack)/2
        global current_z
        current_z=int(middle_slice) #must convert into integer to use for indexing
    
    def display_image(self,z_slice):
        global source_image_width
        global source_image_height
        array=stack[z_slice].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
        new_image=Image.fromarray(array)
        dimensions=array.astype(np.double)
        source_image_width=dimensions.shape[0]
        source_image_height=dimensions.shape[1]
        render=ImageTk.PhotoImage(new_image)
        img=Label(self,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
        img.image=render #.image is a method attribute of Label
        PreviewWindow.right_preview=Canvas(self.master,width=source_image_width,height=source_image_height)
        PreviewWindow.right_preview.grid(row=1,column=1,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
        PreviewWindow.right_preview.create_image(source_image_width/2,source_image_height/2,image=render)
    

    def display_scroll_bar(self,initial=False):
        global right_scroll_bar
        right_scroll_bar=Canvas(self.master,width=source_image_width,height=Window.scroll_bar_height,bg='lightsteelblue')

        right_scroll_bar.grid(row=2,column=1,columnspan=9,padx=5,pady=2.5,sticky=N+S+E+W)

        toggle_half_width=int(source_image_width/len(stack))

        if initial==True:
            right_scroll_bar.create_rectangle(source_image_width/2-toggle_half_width,0,(source_image_width/2)+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue')
            right_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(int(current_z)))

        def scroll_slice(event):
            global conversion_ratio
            if event.x>=1 and event.x<=source_image_width:
                conversion_ratio=len(stack)/source_image_width
                current_z=int(event.x*conversion_ratio)
                return current_z
                
            return None
        
        def move_z_cursor(event):
            global current_z
            nonlocal toggle_half_width
            current_z=scroll_slice(event)
            if current_z!=None and current_z!=0 and current_z<=len(stack):
                
                right_scroll_bar.delete('all')
                right_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                right_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))

                if LockPreview.lock_previews:
                    left_scroll_bar.delete('all')
                    left_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                    left_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))
                
                PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                PreviewWindow.preview_array.view_preview()


            right_scroll_bar.bind('<B1-Motion>',scroll_source_image_stack)
            
            bind_collect_pixels()
        
        def scroll_source_image_stack(event):

            global current_z
            current_z=scroll_slice(event)
            if isinstance(current_z,int):
                if current_z>0:
                    self.display_image(current_z-1) 
                    if SegmentedArray.preview_option:
                        PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                        PreviewWindow.preview_array.view_preview()

                    if LockPreview.lock_previews:
                        source_image_stack.display_image(current_z-1)
                        if SegmentedArray.preview_option:
                            PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                            PreviewWindow.preview_array.view_preview()
                        

            right_scroll_bar.bind('<B1-Motion>',move_z_cursor)
            bind_collect_pixels()

        right_scroll_bar.bind('<B1-Motion>',move_z_cursor)
        bind_collect_pixels()
    
    def display_stack_extremes(self,master=None):
        first_slice_label=Label(master,text='1')
        first_slice_label.grid(row=2,column=0,padx=2,pady=2,sticky=E)
        last_slice=str(len(stack))
        last_slice_label=Label(master,text=last_slice)
        last_slice_label.grid(row=2,column=10,padx=2,pady=2,sticky=W)

class GroupedView(Frame):
    group_preview=None
    listbox_height=25
    group_number_label=None

    def __init__(self,master,foldername,grouping_data):
        Frame.__init__(self,master) #Image module does not work without Frame superclass
        self.master=master
        self.foldername=foldername
        self.grouping_data=grouping_data
        self.__version=1

        os.chdir(directory_name)
        try:
            os.mkdir(self.foldername)
        except FileExistsError:
            pass
        os.chdir(str(self.foldername))

        global group_window
        group_window.deiconify()
    
    def display_grouped_stack(self,z_slice=None):
        if z_slice==None:
            z_slice=math.floor(len(stack)/2)
        try:
            array=self.grouping_data.colored_stack[z_slice]
            new_image=Image.fromarray(np.uint8(array).reshape(source_image_width,source_image_height,3))
            render=ImageTk.PhotoImage(new_image)
            img=Label(self,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
            img.image=render #.image is a method attribute of Label
            GroupedView.group_preview=Canvas(self.master,width=source_image_width,height=source_image_height)
            GroupedView.group_preview.grid(row=1,rowspan=15,column=1,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
            GroupedView.group_preview.create_image(source_image_width/2,source_image_height/2,image=render)
        except IndexError:
            pass

    def display_scroll_bar(self,initial=False):
        global right_scroll_bar
        group_scroll_bar=Canvas(self.master,width=source_image_width,height=Window.scroll_bar_height,bg='lightsteelblue')

        group_scroll_bar.grid(row=16,column=1,columnspan=9,padx=5,pady=2.5,sticky=N+S+E+W)

        toggle_half_width=int(source_image_width/len(stack))

        if initial==True:
            group_scroll_bar.create_rectangle(source_image_width/2-toggle_half_width,0,(source_image_width/2)+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue')
            group_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(int(current_z)))

        def scroll_slice(event):
            global conversion_ratio
            if event.x>=1 and event.x<=source_image_width:
                conversion_ratio=len(stack)/source_image_width
                current_z=int(event.x*conversion_ratio)
                return current_z
                
            return None
        
        def move_z_cursor(event):
            global current_z
            nonlocal toggle_half_width
            current_z=scroll_slice(event)+1
            if current_z!=None and current_z!=0 and current_z<=len(stack):
                
                group_scroll_bar.delete('all')
                group_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                group_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))

                self.display_grouped_stack(z_slice=current_z)
                


            group_scroll_bar.bind('<B1-Motion>',scroll_source_image_stack)
            
            bind_collect_pixels()
        
        def scroll_source_image_stack(event):

            global current_z
            current_z=scroll_slice(event)
            if isinstance(current_z,int):
                if current_z>0:
                    self.display_grouped_stack(current_z-1) 

            group_scroll_bar.bind('<B1-Motion>',move_z_cursor)
            bind_collect_pixels()

        group_scroll_bar.bind('<B1-Motion>',move_z_cursor)
        bind_collect_pixels()
    
    def display_stack_extremes(self,master=None):
        first_slice_label=Label(master,text='1')
        first_slice_label.grid(row=16,column=0,padx=2,pady=2,sticky=E)
        last_slice=str(len(stack))
        last_slice_label=Label(master,text=last_slice)
        last_slice_label.grid(row=16,column=10,padx=2,pady=2,sticky=W)

    def display_data_table(self,color_scheme):

        def go_to_next_page():
            try:
                next_page=DataTable.current_page+1
                if (next_page*22)<len(self.grouping_data.group_information)+22:
                    data_table=DataTable(master=group_window,data=self.grouping_data.group_information,color_scheme=color_scheme,page=next_page)
            except:
                pass
        
        def go_to_previous_page():
            try:
                previous_page=DataTable.current_page-1
                if previous_page<1:
                    return
                data_table=DataTable(master=group_window,data=self.grouping_data.group_information,color_scheme=color_scheme,page=previous_page)
            except:
                pass

        data_table=DataTable(master=group_window,data=self.grouping_data.group_information,color_scheme=color_scheme)
        previous_page_button=Button(master=group_window,text=' < ',command=go_to_previous_page)
        previous_page_button.grid(row=12,column=11,padx=5,pady=5,sticky='W')
        next_page_button=Button(master=group_window,text=' > ',command=go_to_next_page)
        next_page_button.grid(row=12,column=17,padx=5,pady=5,sticky='E')

    def display_buttons(self):

        GroupedView.group_number_label=Label(master=self.master,text='')
        GroupedView.group_number_label.grid(row=0,column=1,padx=5,pady=5)
        

        calculate_width_button=Button(master=self.master,text='Calculate width',command=enable_calculate_widths)
        calculate_width_button.grid(row=0,column=12,padx=5,pady=5)
        select_color_scheme_label=Label(master=self.master,text='Color schemes')
        select_color_scheme_label.grid(row=1,column=18,padx=5,pady=5)
        color_scheme_listbox=Listbox(master=self.master)
        color_scheme_listbox.grid(row=2,column=18,padx=5,pady=5)
        color_scheme_listbox.configure(height=7,width=15)
        
        for color_scheme in color_scheme_dictionary.keys():
            color_scheme_listbox.insert(0,color_scheme)
        
        def select_color_scheme(event):
            global color_scheme_choice
            color_scheme_listbox=event.widget
            index = int(color_scheme_listbox.curselection()[0])
            color_scheme_choice=color_scheme_listbox.get(index)
            change_color_scheme_button.config(state=NORMAL)
        
        def change_color_scheme():
            global color_scheme
            color_scheme=color_scheme_dictionary[color_scheme_choice]
            if shuffle_colors:
                random.shuffle(color_scheme)
            groups.color_groups(color_scheme=color_scheme)
            self.display_grouped_stack(z_slice=current_z)
            self.display_data_table(color_scheme=color_scheme)
        
        def shuffle_the_colors():
            global shuffle_colors
            shuffle_colors=True
            change_color_scheme()
        

        
        color_scheme_listbox.bind('<<ListboxSelect>>', select_color_scheme)

        change_color_scheme_button=Button(master=self.master,text='Change color scheme',command=change_color_scheme)
        change_color_scheme_button.grid(row=3,column=18,padx=5,pady=5)
        change_color_scheme_button.config(state=DISABLED)
        shuffle_colors_button=Button(master=self.master,text='Shuffle colors',command=shuffle_the_colors)
        shuffle_colors_button.grid(row=4,column=18,padx=5,pady=5)

        def show_color_scheme_info():
                message='''
You can change the color scheme from the drop-down box and shuffle the colors. Changes will be automatically applied to images in the folder 'differentiated_elements_colored'.
'''+str(email_string)
                messagebox.showinfo(title='Color schemes',message=message)

        color_scheme_info_button=Button(master=self.master,text='i',width=3,command=show_color_scheme_info)
        color_scheme_info_button.grid(row=1,column=20,columnspan=2,padx=5,pady=5)

    

    
    



        

class DataTable(object):
    width=75
    height=500
    cell_height=15
    group_count=1

    current_page=1

    def __init__(self,master,data,color_scheme,page=1):
        self.master=master
        self.data=data
        self.page_index=(page*22)-22
        self.__version=1
        DataTable.current_page=page

        row_length=len(self.data)

        applied_color_scheme=[]
        for number in Grouping.color_index:
            r=color_scheme[number][0]
            g=color_scheme[number][1]
            b=color_scheme[number][2]
            hex_color=rgb2hex(r,g,b)
            applied_color_scheme.append(hex_color)

        self.id_canvas=Canvas(master=self.master,width=DataTable.width,height=DataTable.height,bg='white')
        self.id_canvas.grid(row=1,rowspan=10,column=11,columnspan=1,padx=5,pady=5,sticky=N+S+E+W)
        self.vol_canvas=Canvas(master=self.master,width=DataTable.width,height=DataTable.height,bg='white')
        self.vol_canvas.grid(row=1,rowspan=10,column=12,columnspan=1,padx=5,pady=5,sticky=N+S+E+W)
        
        
        self.id_canvas.create_text(DataTable.width/2,DataTable.cell_height,text='ID\n',font=('Helvetica',12,'bold'))
        self.vol_canvas.create_text(DataTable.width/2,DataTable.cell_height,text='Volume\n (voxels)',font=('Helvetica',12,'bold'))
        

        self.id_canvas.create_rectangle(0,30,DataTable.width,DataTable.cell_height*26,fill='black')
        self.vol_canvas.create_rectangle(0,30,DataTable.width,DataTable.cell_height*26,fill='black')
        

        review_button=Button(master=self.master,text='Review elements',command=self.review_groups)
        review_button.grid(row=0,column=11,padx=5,pady=5,sticky=W)

        def show_review_info():
                message='''
Separate elements are color-coded here and the volume (voxels) measurements are reported in descending order of volume. 
The images can be found in the folder 'differentiated_elements_colored' and the measurements can be found in the folder 'quantitation'.

You can visually-inspect each element in order using Review elements or by clicking on elements in the table.

You can calculate the maximum width of the elements in 3D. The width will be indicated with yellow lines on the 2D display but note that the maximum width may not be parallel to the image plane.

Caution: in order to accurately calculate the width of elements, the original voxel dimensions must be cubic (X=Y=Z). 
'''+str(email_string)
                messagebox.showinfo(title='Review elements',message=message)

        review_info_button=Button(master=self.master,text='i',width=3,command=show_review_info)
        review_info_button.grid(row=0,column=20,columnspan=2,padx=5,pady=5,sticky=N+W)

        standardised_row=1
        for row in range(self.page_index,self.page_index+22):
            if row<row_length:
                self.id_canvas.create_text(DataTable.width/2,45+DataTable.cell_height*standardised_row,text=str(self.data[row][0]),font=('Helvetica',12,'normal'),fill=applied_color_scheme[row])
                self.vol_canvas.create_text(DataTable.width/2,45+DataTable.cell_height*standardised_row,text=str(self.data[row][1]),font=('Helvetica',12,'normal'),fill=applied_color_scheme[row])
                standardised_row+=1
        
        
        self.id_canvas.bind('<Button-1>',self.hover_over)
        self.vol_canvas.bind('<Button-1>',self.hover_over)
        
        
        
    
    def hover_over(self,event):
        first_appearance_z=current_z #declared
        last_appearance_z=current_z #declared
        height=(event.y-45)
        row=int(height/DataTable.cell_height)+(self.page_index)
        
        group_number=self.data[row][0]

        for row in groups.group_information:
            if group_number==row[0]:
                first_appearance_z=row[2]
                last_appearance_z=row[3]
        
        max_size=[[0],0,None] #[all_pieces,z,array]
        for z in range (int(first_appearance_z),int(last_appearance_z+1)):
            array=groups.grouping_of_stack[first_appearance_z]
            all_pieces=Grouping.find_all_pieces(array,group_number)
            if all_pieces!=None:
                if len(all_pieces)>len(max_size[0]):
                    max_size=[all_pieces,z,array]
        
        all_pieces=max_size[0]
        z_choice=max_size[1]
        array=max_size[2]
        
        grouped_view.display_grouped_stack(z_slice=z_choice)
        
        if all_pieces!=None:
            perimeter_pieces=Grouping.find_perimeter_pieces(array,all_pieces)
            for [row,col] in perimeter_pieces:
                GroupedView.group_preview.create_rectangle(col,row,col,row,fill='green2',outline='green2')
        
        GroupedView.group_number_label.config(text='Element '+str(group_number))
        
        
    
    def review_groups(self):
        group_number=int(DataTable.group_count)
        first_appearance_z=current_z #declared
        for row in groups.group_information:
            
            if group_number==row[0]:
                first_appearance_z=row[2]
        grouped_view.display_grouped_stack(z_slice=first_appearance_z)
        array=groups.grouping_of_stack[first_appearance_z]
    
        all_pieces=Grouping.find_all_pieces(array,group_number)
        if all_pieces!=None:
            perimeter_pieces=Grouping.find_perimeter_pieces(array,all_pieces)
            for [row,col] in perimeter_pieces:
                GroupedView.group_preview.create_rectangle(col,row,col,row,fill='green2',outline='green2')
            
            DataTable.group_count+=1
        else:
            found=False
            for z in range(0,len(stack)):
                present=np.argwhere(groups.grouping_of_stack[z]==group_number)
                if present.size>0:
                    first_appearance_z=z
                    found=True
                    break
            if not found:
                pass
        
        GroupedView.group_number_label.config(text='Element '+str(group_number))

class SegmentedView(Frame): #SegmentedView class is used to display the segmented layers

    scroll_bar_height=35
    segmented_vol_segmented_canvas=None
    segmented_vol_canvas_number=1
    segmented_vol_segmented_canvas1=None
    segmented_vol_segmented_canvas2=None
    segmented_vol_segmented_stack=[]
    selection_coordinates=[]
    point_iterator=0
    point_iterator_max=10
    show_input_image=True
    show_segmentation=True
    segmented_vol_z_start_entry=False
    segmented_vol_z_end_entry=False
    mini_seg_lower_threshold_entry=None
    mini_seg_upper_threshold_entry=None
    mini_seg_minimum_width_entry=None
    mini_seg_threshold_selection=[]
    segmented_vol_filter_size_entry=None
    sigma_entry=None
    sigma_preview=0
    sigma_label=None
    smoothen_toggle=True
    Gaussian_toggle=True
    gauss_button=None
    smoothen_button=None
    smoothen_factor_entry=None

    
    @staticmethod
    def get_segmented_vol_canvas():
        if SegmentedView.segmented_vol_canvas_number==1:
            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.segmented_vol_segmented_canvas2
        elif SegmentedView.segmented_vol_canvas_number==2:
            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.segmented_vol_segmented_canvas1
        return SegmentedView.segmented_vol_segmented_canvas
    
    @staticmethod
    def validate_selection_coordinates():
        for coord in SegmentedView.selection_coordinates:
            if coord.x_pos<0:
                coord.x_pos==0
            elif coord.x_pos>source_image_width-1:
                coord.x_pos=source_image_width-1
            if coord.y_pos<0:
                coord.y_pos==0
            elif coord.y_pos>source_image_height-1:
                coord.y_pos=source_image_height-1
    
    @staticmethod
    def delete_selection_coordinates():
        SegmentedView.selection_coordinates=[]

    @staticmethod
    def save_segmented_vol_segmented_stack(file_suffix=''):
            foldername='segmented_volume'+file_suffix
            Files.change_and_check_directory(workspace_filename)
            Files.change_and_overwrite_directory(foldername,parent_directory=False)
            count=0
            for plane in SegmentedView.segmented_vol_segmented_stack:
                image=Image.fromarray(plane.image_array)
                string_z_pos=StringZ.int_to_3_dec_string(count)
                image.save(string_z_pos+'.tif')
                count+=1

            LogWindow.update_log('Saved segmented volume to folder: '+str(foldername))

    @staticmethod
    def segmented_vol_change_z_to_0():
        SegmentedView.segmented_vol_z_start_entry.delete(0,END)
        SegmentedView.segmented_vol_z_start_entry.insert(0,'1')
    
    @staticmethod
    def segmented_vol_change_z_to_end():
        SegmentedView.segmented_vol_z_end_entry.delete(0,END)
        SegmentedView.segmented_vol_z_end_entry.insert(0,str(len(SegmentedView.segmented_vol_segmented_stack)))

    @staticmethod
    def segmented_vol_only_use_current_z():
        SegmentedView.segmented_vol_z_start_entry.delete(0,END)
        SegmentedView.segmented_vol_z_start_entry.insert(0,str(current_z))
        SegmentedView.segmented_vol_z_end_entry.delete(0,END)
        SegmentedView.segmented_vol_z_end_entry.insert(0,str(current_z))

    @staticmethod
    def open_grouped_view():
        try:
            group_voxels(import_option=True)
        except:
            error_message='Error: You have not yet differentiated the elements in your segmented volume.\n\nDifferentiating the elements will allow you to study individual segments and quantitate them. You should differentiate the elements once you have completed the segmentation. \n\nWould you like to differentiate the elements now?'
            differentiate_elements=messagebox.askokcancel('Elements undifferentiated',error_message)
            if differentiate_elements:
                group_voxels()




    def __init__(self,foldername,RGBA,volume_feature,column,master=None): #master denotes the Tkinter window
        Frame.__init__(self,master) #Image module does not work without Frame superclass
        self.master=master
        self.foldername=foldername
        self.volume_feature=volume_feature
        self.column=column
        self.RGBA=RGBA
        self.segmented_stack=[]
        self.__version=1
        
        global load_image

        self.segmented_stack=SegmentedView.segmented_vol_segmented_stack

        Files.change_and_check_directory(workspace_filename,str(self.foldername))


        file_count=len([name for name in os.listdir('.') if os.path.isfile(name)])
        plane=0
        while plane<file_count:
            string_z_pos=StringZ.int_to_3_dec_string(plane)
            load_image=Image.open(str(string_z_pos)+'.tif') #import the image
            try: #convert it to an rgb image in the first instance
                next_array=np.array(load_image,dtype='bool').reshape(source_image_width,source_image_height) #load as unsigned integers of 8 bit (0 - 255 without + or - signs)
                rgb_list=[]
                for value in np.nditer(next_array):
                    if value:
                        rgb_list.append(RGBA)
                    else:
                        rgb_list.append((0,0,0,0))
                rgb_array=np.array(rgb_list,dtype=np.uint8).reshape(source_image_width,source_image_height,4)
                array_object=PixelArray(rgb_array) #additional data stored in object form, such as version number
            except: #already saved as an rgb image for future instances
                next_array=np.array(load_image,dtype=np.uint8)
                array_object=PixelArray(next_array)
            self.segmented_stack.append(array_object)
            log_window_progress_bar.create_z_progress(plane,len(stack))
            plane=plane+1
            if plane>len(stack):
                break #failsafe to prevent infinite loop if folder is modified to contain more files than the length of the stack
        log_window_progress_bar.hide_z_progress()
    
        
        middle_slice=len(self.segmented_stack)/2
        global current_z        
        current_z=int(middle_slice) #must convert into integer to use for indexing


    def display_image(self,z_slice):
        usage()
        
        if self.volume_feature=='Segmented_Vol':
            self.segmented_stack=SegmentedView.segmented_vol_segmented_stack
            segmented_vol_segmented_window.deiconify()

            if SegmentedView.segmented_vol_canvas_number==1:
                
                SegmentedView.segmented_vol_segmented_canvas1=Canvas(self.master,width=source_image_width,height=source_image_height)
                SegmentedView.segmented_vol_segmented_canvas1.grid(row=1,rowspan=20,column=self.column,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
                SegmentedView.segmented_vol_segmented_canvas1.create_rectangle(0,0,source_image_width,source_image_height,fill='black') #black background
                
                if SegmentedView.show_input_image:
                    try:
                        stack_array=stack[z_slice].image_array
                    except IndexError:
                        try:
                            stack_array=stack[z_slice-1].image_array
                        except IndexError:
                            stack_array=stack[z_slice+1].image_array
    
                    stack_image=Image.fromarray(stack_array)
                    stack_render=ImageTk.PhotoImage(stack_image)
                    stack_img=Label(self.master,image=stack_render) #need to assign it to a Label so that you can specify its grid coordinates below.
                    stack_img.image=stack_render #.image is a method attribute of Label
                    SegmentedView.segmented_vol_segmented_canvas1.create_image(source_image_width/2,source_image_height/2,image=stack_render)
                
                
                if SegmentedView.show_segmentation:
                    try:
                        array=self.segmented_stack[z_slice].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
                    except IndexError:
                        try:
                            array=self.segmented_stack[z_slice-1].image_array
                        except:
                            array=self.segmented_stack[z_slice+1].image_array

                    new_image=Image.fromarray(array)
                    render=ImageTk.PhotoImage(new_image)
                    img=Label(self.master,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
                    img.image=render #.image is a method attribute of Label
                    SegmentedView.segmented_vol_segmented_canvas1.create_image(source_image_width/2,source_image_height/2,image=render)
                
                try:
                    SegmentedView.segmented_vol_segmented_canvas2.delete('all')
                except:
                    pass
                
                SegmentedView.segmented_vol_canvas_number=2

            elif SegmentedView.segmented_vol_canvas_number==2:
                
                SegmentedView.segmented_vol_segmented_canvas2=Canvas(self.master,width=source_image_width,height=source_image_height)
                SegmentedView.segmented_vol_segmented_canvas2.grid(row=1,rowspan=20,column=self.column,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
                SegmentedView.segmented_vol_segmented_canvas2.create_rectangle(0,0,source_image_width,source_image_height,fill='black') #black background
                SegmentedView.segmented_vol_canvas_number=1

                if SegmentedView.show_input_image:
                    try:
                        stack_array=stack[z_slice].image_array
                    except IndexError:
                        stack_array=stack[z_slice-1].image_array
                    stack_image=Image.fromarray(stack_array)
                    stack_render=ImageTk.PhotoImage(stack_image)
                    stack_img=Label(self.master,image=stack_render) #need to assign it to a Label so that you can specify its grid coordinates below.
                    stack_img.image=stack_render #.image is a method attribute of Label
                    SegmentedView.segmented_vol_segmented_canvas2.create_image(source_image_width/2,source_image_height/2,image=stack_render)
                
                if SegmentedView.show_segmentation:
                    array=self.segmented_stack[z_slice].image_array #isolate the image_array attribute of the object created by PixelArray so that dimensions can be measured
                    new_image=Image.fromarray(array)
                    render=ImageTk.PhotoImage(new_image)
                    img=Label(self.master,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
                    img.image=render #.image is a method attribute of Label
                    SegmentedView.segmented_vol_segmented_canvas2.create_image(source_image_width/2,source_image_height/2,image=render)
                

                try:
                    SegmentedView.segmented_vol_segmented_canvas1.delete('all')
                except:
                    pass
        
        else:
            raise Exception('Invalid volume_feature')

    def apply_temporary_Gaussian_filter(self):
        global temp_stack_storage
        if len(temp_stack_storage)==0:
            temp_stack_storage=copy.deepcopy(stack)
        for z in range(0,len(stack)):
            stack[z].image_array=gaussian_filter(stack[z].image_array,1)
        SegmentedView.sigma_preview+=1
        SegmentedView.sigma_label.config(text='σ = '+str(SegmentedView.sigma_preview))
        

        self.display_image(current_z)
    
    def reverse_Gaussian_filter(self):
        global temp_stack_storage
        for z in range(0,len(stack)):
            stack[z].image_array=temp_stack_storage[z].image_array
        del temp_stack_storage
        gc.collect()
        temp_stack_storage=[]
        SegmentedView.sigma_preview=0
        SegmentedView.sigma_label.config(text='')
        self.display_image(current_z)

    def display_scroll_bar(self,initial=False):
        if int(self.column)==1:
            global left_scroll_bar
            relevant_scroll_bar=left_scroll_bar
        else:
            global right_scroll_bar
            relevant_scroll_bar=right_scroll_bar
        relevant_scroll_bar=Canvas(self.master,width=source_image_width,height=Window.scroll_bar_height,bg='lightsteelblue')

        relevant_scroll_bar.grid(row=21,column=self.column,columnspan=9,padx=5,pady=2.5,sticky=N+S+E+W)

        toggle_half_width=int(source_image_width/len(stack))

        if initial==True:
            relevant_scroll_bar.create_rectangle(source_image_width/2-toggle_half_width,0,(source_image_width/2)+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue')
            relevant_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(int(current_z)))

        def scroll_slice(event):
            global conversion_ratio
            if event.x>=1 and event.x<=source_image_width:
                conversion_ratio=len(stack)/source_image_width
                current_z=int(event.x*conversion_ratio)
                if current_z==0:
                    current_z=1
                return current_z
            return None

        
        def move_z_cursor(event):
            nonlocal toggle_half_width
            global current_z
            global current_z_left
            current_z=scroll_slice(event)
            current_z_left=current_z
            if current_z!=None and current_z!=0 and current_z<=len(stack):
                
                relevant_scroll_bar.delete('all')
                relevant_scroll_bar.create_rectangle(event.x-toggle_half_width,0,event.x+toggle_half_width,Window.scroll_bar_height,fill='steelblue',outline='steelblue') #scroll button
                relevant_scroll_bar.create_text(source_image_width/2,(Window.scroll_bar_height/2),text=str(current_z))

            relevant_scroll_bar.bind('<B1-Motion>',scroll_segmented_layer,add='+')
            self.update_idletasks()
            #relevant_scroll_bar.bind('<Left>',scroll_segmented_layer,add='+')
            #relevant_scroll_bar.focus_set()
            bind_collect_pixels()
        
        def scroll_segmented_layer(event):
            current_z=scroll_slice(event)
            if isinstance(current_z,int):
                if current_z>0:
                    self.display_image(current_z-1)

                    if LockPreview.lock_previews:
                        preview.display_image(current_z-1)
                        if SegmentedArray.preview_option:
                            PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array,master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                            PreviewWindow.preview_array.view_preview()


            relevant_scroll_bar.bind('<B1-Motion>',move_z_cursor)
            bind_collect_pixels()

        relevant_scroll_bar.bind('<B1-Motion>',move_z_cursor)
        bind_collect_pixels()
        
    def display_stack_extremes(self):
        first_slice_label=Label(self.master,text='1')
        first_slice_label.grid(row=21,column=self.column-1,padx=10,pady=5,sticky=E)
        last_slice=str(len(stack))
        last_slice_label=Label(self.master,text=last_slice)
        last_slice_label.grid(row=21,column=self.column+9,padx=10,pady=5,sticky=W)
    
    def display_stack_button(self):
        if self.volume_feature=='Segmented_Vol':
            display_parameters_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Display parameters________________')
            display_parameters_header.grid(row=1,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)


            stack_button=Button(master=self.master,text='View source',command=self.switch_stack_segmented_vol)
            stack_button.grid(row=2,column=self.column+9,columnspan=2,padx=5,pady=5,sticky=N+W)

            Gauss_button=Button(master=self.master,text='Gaussian blur',width=12,command=self.apply_temporary_Gaussian_filter)
            Gauss_button.grid(row=2,column=self.column+11,columnspan=2,padx=5,pady=5,sticky=N+W)
            SegmentedView.sigma_label=Label(master=self.master,text='')
            SegmentedView.sigma_label.grid(row=2,column=self.column+13,columnspan=2,padx=5,pady=5,sticky=N+W)
            reverse_Gauss_button=Button(master=self.master,text='Restore',width=10,command=self.reverse_Gaussian_filter)
            reverse_Gauss_button.grid(row=2,column=self.column+15,columnspan=2,padx=5,pady=5,sticky=N+W)

            def show_display_parameters_info():
                message='''
If your source image is too grainy, you can apply a Gaussian blur to smoothen it.
This can be useful when doing local segmentation: it can be difficult to pick up all the pixels in the desired range if the source image is too grainy, but blurring the image can help.

Repeatedly click the Gaussian blur button to increase the σ factor.

The original source image can be restored with the Restore button.
'''+str(email_string)
                messagebox.showinfo(title='Gaussian blur',message=message)

            display_parameters_info_button=Button(master=self.master,text='i',width=3,command=show_display_parameters_info)
            display_parameters_info_button.grid(row=2,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)
    
    def display_layer_button(self):
        if self.volume_feature=='Segmented_Vol':
            stack_button=Button(master=self.master,text='View segment',command=self.switch_layer_segmented_vol)
            stack_button.grid(row=2,column=self.column+17,columnspan=2,padx=5,pady=5,sticky=N+W)
    
    def display_edit_buttons(self):
        if self.volume_feature=='Segmented_Vol':
            draw_erase_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Draw/erase________________________')
            draw_erase_header.grid(row=10,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)
            rect_fill_button=Button(master=self.master,text='Rectangular fill',command=self.enable_fill_rectangle_segmented_vol)
            rect_fill_button.grid(row=11,column=self.column+9,columnspan=2,padx=5,pady=5,sticky=N+W)
            rect_erase_button=Button(master=self.master,text='Rectangular erase',command=self.enable_erase_segmented_vol)
            rect_erase_button.grid(row=11,column=self.column+11,columnspan=2,padx=5,pady=5,sticky=N+W)
            
            point_fill_button=Button(master=self.master,text='Point fill',command=self.enable_point_fill_segmented_vol)
            point_fill_button.grid(row=11,column=self.column+14,columnspan=2,padx=5,pady=5,sticky=W)
            
            point_erase_button=Button(master=self.master,text='Point erase',command=self.enable_point_erase_segmented_vol)
            point_erase_button.grid(row=11,column=self.column+16,columnspan=2,padx=5,pady=5,sticky=W)
            
            def show_draw_erase_info():
                message='''
Rectangular draw/erase

Click on fill or erase and then mouse-click once on the source image. A red spot will appear and will mark one corner of the rectangle.
Mouse-click once more elsewhere on the source image to place another corner of the rectangle. The fill/erase changes will be applied.

Point draw/erase

Click on fill or erase and then mouse-click and press down on the source image to draw or wipe segmented features. Filled in segments appear temporarily blue and erased segments appear temporarily red.
The point size can be altered with the scroll bar. Diameter: 1-17 pixels

The z boundaries can be altered in the Z selection section.
'''+str(email_string)
                messagebox.showinfo(title='Draw/erase',message=message)
            
            draw_erase_info_button=Button(master=self.master,text='i',width=3,command=show_draw_erase_info)
            draw_erase_info_button.grid(row=11,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)

            def show_point_size_when_scrolling(event):
                global point_display
                global point_size
                
                try:
                    if point_display is not None:
                        point_size_scroll_bar.delete(point_display)

                except:
                    pass
                
                
                step_size=math.floor((event.x-10)/25)
                if step_size>9:
                    step_size=9
                elif step_size<1:
                    step_size=1
                point_size=step_size
                point_display=point_size_scroll_bar.create_oval(\
                    (step_size*25)-step_size,\
                        30-step_size,\
                            (step_size*25)+step_size,\
                                30+step_size,\
                                    fill='magenta',outline='black') 
                rangegram.bind('<B1-Motion>',rangegram_data.select_boundary)

            
            point_size_scroll_bar=Canvas(master=self.master,width=320,height=60,bg='white')
            point_size_scroll_bar.grid(row=12,column=14,columnspan=5,padx=5,pady=5)
            point_size_scroll_bar.bind('<B1-Motion>',show_point_size_when_scrolling)
            point_size_scroll_bar.create_rectangle(25,29,225,31,fill='snow3',outline='')

            global point_display
            step_size=6 #default
            point_display=point_size_scroll_bar.create_oval(\
                (step_size*25)-step_size,\
                    30-step_size,\
                        (step_size*25)+step_size,\
                            30+step_size,\
                                fill='magenta',outline='black') 

            z_selection_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Z selection________________________')
            z_selection_header.grid(row=4,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)
            z_start_button=Button(master=self.master,text='Start',command=SegmentedView.segmented_vol_change_z_to_0)
            z_start_button.grid(row=5,column=self.column+10,padx=5,pady=5)
            SegmentedView.segmented_vol_z_start_entry=Entry(master=self.master,width=3)
            SegmentedView.segmented_vol_z_start_entry.grid(row=5,column=self.column+11,padx=5,pady=5)
            SegmentedView.segmented_vol_z_start_entry.insert(0,'1')
            left_colon_label=Label(master=self.master,text=':')
            left_colon_label.grid(row=5,column=self.column+12,padx=5,pady=5)
            z_middle_button=Button(master=self.master,text='Current',command=SegmentedView.segmented_vol_only_use_current_z)
            z_middle_button.grid(row=5,column=self.column+13,columnspan=2,padx=5,pady=5)
            right_colon_label=Label(master=self.master,text=':')
            right_colon_label.grid(row=5,column=self.column+15,padx=5,pady=5)
            SegmentedView.segmented_vol_z_end_entry=Entry(master=self.master,width=3)
            SegmentedView.segmented_vol_z_end_entry.grid(row=5,column=self.column+16,padx=5,pady=5)
            SegmentedView.segmented_vol_z_end_entry.insert(0,str(len(SegmentedView.segmented_vol_segmented_stack)))
            z_end_button=Button(master=self.master,text='End',command=SegmentedView.segmented_vol_change_z_to_end)
            z_end_button.grid(row=5,column=self.column+17,padx=5,pady=5)

            def show_z_selection_info():
                message='''
Any changes made in the Local segmentation or Draw/erase sections will only occur in the Z stack range specified here. Changes made in other sections will apply to the whole Z stack.

Start sets the minimum z to the start of the stack
Current sets the minimum z and maximum z to the current z plane
End sets the maximum z to the end of the stack
Set lowZ sets the minimum z to the current z plane
Set highZ sets the maximum z to the current z plane
The minimum z and maximum z can be manually altered in the entry fields.
'''+str(email_string)
                messagebox.showinfo(title='Z selection',message=message)
            
            z_selection_info_button=Button(master=self.master,text='i',width=3,command=show_z_selection_info)
            z_selection_info_button.grid(row=5,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)

            mini_seg_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Local segmentation________________')
            mini_seg_header.grid(row=7,column=self.column+9,columnspan=10,sticky=W)
            mini_seg_rect_button=Button(master=self.master,text='Select',command=self.mini_seg_enable_draw_rectangle)
            mini_seg_rect_button.grid(row=8,column=self.column+10,columnspan=2)
            SegmentedView.mini_seg_lower_threshold_entry=Entry(master=self.master,width=3)
            SegmentedView.mini_seg_lower_threshold_entry.grid(row=8,column=self.column+12)
            mini_seg_lower_threshold_set_button=Button(master=self.master,text='Set lowZ',command=self.set_lower_z)
            mini_seg_lower_threshold_set_button.grid(row=6,column=self.column+10)
            mini_seg_colon=Label(master=self.master,text=':')
            mini_seg_colon.grid(row=8,column=self.column+13)
            SegmentedView.mini_seg_upper_threshold_entry=Entry(master=self.master,width=3)
            SegmentedView.mini_seg_upper_threshold_entry.grid(row=8,column=self.column+14)
            mini_seg_upper_threshold_set_button=Button(master=self.master,text='Set highZ',command=self.set_upper_z)
            mini_seg_upper_threshold_set_button.grid(row=6,column=self.column+17)
            mini_seg_minimum_width_label=Label(master=self.master,text='Min width')
            mini_seg_minimum_width_label.grid(row=8,column=self.column+15,columnspan=2,sticky=NSEW)
            SegmentedView.mini_seg_minimum_width_entry=Entry(master=self.master,width=3)
            SegmentedView.mini_seg_minimum_width_entry.grid(row=8,column=self.column+17)
            mini_seg_refresh_button=Button(master=self.master,text='Refresh',command=self.refresh_threshold)
            mini_seg_refresh_button.grid(row=9,column=self.column+15,columnspan=1,padx=5,pady=5,sticky=NSEW)
            mini_seg_segment_button=Button(master=self.master,text='Segment',command=self.mini_segment)
            mini_seg_segment_button.grid(row=9,column=self.column+17,columnspan=1,padx=5,pady=5,sticky=NSEW)

            def show_local_segmentation_info():
                message='''
Local segmentation is used to segment features based on threshold intensity and minimum width within a rectangular region of interest.

To select a region of interest, click Select and then mouse-click once on the image. An orange dot will appear and will mark one corner of the rectangle.
Mouse-click once elsewhere on the image to set another corner of the rectangle. The xy boundaries of the region of interest will appear. The z boundaries can be altered in the Z selection section.

Next, click and press down on the feature you want to segment. Move the cursor while pressing down and this will act as an "eye dropper" to determine the range of pixel intensities included in the threshold range. Pixels within the range will appear green. The lower and upper thresholds can also be manually altered in the fields.

Optional: apply a minimum width to exclude noise and other small matter. The width is in pixels/voxels. Recommended values: 3-10

Click Refresh to select a new threshold range within the same region of interest. Click Segment to apply the segmentation.
'''+str(email_string)
                messagebox.showinfo(title='Local segmentation',message=message)
            
            local_segmentation_info_button=Button(master=self.master,text='i',width=3,command=show_local_segmentation_info)
            local_segmentation_info_button.grid(row=8,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)
           

            save_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Save edits to file___________________')
            save_header.grid(row=13,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)
            save_button=Button(master=self.master,text='Save',width=5,command=SegmentedView.save_segmented_vol_segmented_stack)
            save_button.grid(row=14,column=self.column+9,padx=5,pady=5,sticky=N+W)
            differentiate_elements_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Differentiate elements_____________')
            differentiate_elements_header.grid(row=15,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)
            group_pixels_button=Button(master=self.master,text='Differentiate elements',command=group_voxels)
            group_pixels_button.grid(row=16,column=self.column+9,columnspan=4,padx=5,pady=5,sticky=W)
            open_grouped_view=Button(master=self.master,text='View elements',command=SegmentedView.open_grouped_view)
            open_grouped_view.grid(row=16,column=self.column+15,columnspan=4,padx=5,pady=5,sticky=W)
            filter_groups_button=Button(master=self.master,text='Filter elements',command=enable_filter_groups)
            filter_groups_button.grid(row=17,column=self.column+9,columnspan=4,padx=5,pady=5,sticky=W)
            minimum_label=Label(master=self.master,text='Minimum')
            minimum_label.grid(row=17,column=self.column+15,padx=2,pady=5,sticky=E)
            SegmentedView.segmented_vol_filter_size_entry=Entry(master=self.master,width=6)
            SegmentedView.segmented_vol_filter_size_entry.grid(row=17,column=self.column+16,padx=3,pady=5,sticky=W)
            SegmentedView.segmented_vol_filter_size_entry.insert(0,str(1000))
            pixels_label=Label(master=self.master,text='voxels')
            pixels_label.grid(row=17,column=self.column+17,padx=3,pady=5,sticky=W)

            def show_differentiate_elements_info():
                message='''
After you have finished editing the segmented volume, you can differentiate the elements. The elements can then be color-coded and quantitated (e.g. volume). 
The images will be saved to the folder 'differentiated_elements' and 'differentiated_elements_colored'. 
Measurements will be saved to the folder 'quantitation'.

Click View elements to display the color-coded elements and measurements in a new window. Once you have differentiated the elements, you can reopen this window in saved workspaces.

Filter elements can be used to exclude elements containing fewer than a specified number of voxels (default 1000). The number can be altered in the field. 
The images will be saved to the folder 'differentiated_elements_filtered'. 
Filtered measurements will be saved to the folder 'quantitation' and all the measurements will be saved to the folder 'quantitaton_unfiltered'.

Tip: Don't waste time removing small bits of noise from the segmented volume. All the noise can be removed in one go with Filter elements.
'''+str(email_string)
                messagebox.showinfo(title='Differentiate elements',message=message)
            
            differentiate_elements_info_button=Button(master=self.master,text='i',width=3,command=show_differentiate_elements_info)
            differentiate_elements_info_button.grid(row=16,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)
            
            final_touches_header=Label(master=self.master,fg='gray50',font="TkDefaultFont 12 bold",text='________________________________________________________________Final touches______________________')
            final_touches_header.grid(row=18,column=self.column+9,columnspan=10,padx=5,pady=5,sticky=W)
            
            def change_smoothen_toggle():
                if SegmentedView.smoothen_toggle==True:
                    SegmentedView.smoothen_toggle=False
                    SegmentedView.smoothen_button.config(text='Smoothen OFF')
                else:
                    SegmentedView.smoothen_toggle=True
                    SegmentedView.smoothen_button.config(text='Smoothen ON')
                
            
            def change_Gaussian_toggle():
                if SegmentedView.Gaussian_toggle==True:
                    SegmentedView.Gaussian_toggle=False
                    SegmentedView.gauss_button.config(text='Gaussian filter OFF')
                else:
                    SegmentedView.Gaussian_toggle=True
                    SegmentedView.gauss_button.config(text='Gaussian filter ON')
            
            SegmentedView.gauss_button=Button(master=self.master,text='Gaussian filter ON',command=change_Gaussian_toggle)
            SegmentedView.gauss_button.grid(row=19,column=self.column+13,columnspan=3,padx=5,pady=5,sticky=W)
            sigma_label=Label(master=self.master,text='Sigma')
            sigma_label.grid(row=19,column=self.column+16,sticky=W)
            SegmentedView.sigma_entry=Entry(master=self.master,width=2)
            SegmentedView.sigma_entry.grid(row=19,column=self.column+17,sticky=W)
            SegmentedView.sigma_entry.insert(0,'1')
            SegmentedView.smoothen_button=Button(master=self.master,text='Smoothen ON',command=change_smoothen_toggle)
            SegmentedView.smoothen_button.grid(row=19,column=self.column+9,columnspan=2,padx=5,pady=5,sticky=W)
            smoothen_factor_label=Label(master=self.master,text='Factor')
            smoothen_factor_label.grid(row=19,column=self.column+11,padx=5,pady=5)
            SegmentedView.smoothen_factor_entry=Entry(master=self.master,width=2)
            SegmentedView.smoothen_factor_entry.grid(row=19,column=self.column+12,padx=5,pady=5)
            SegmentedView.smoothen_factor_entry.insert(0,'3')
            apply_final_touches_button=Button(master=self.master,text='Apply',command=enable_apply_final_touches)
            apply_final_touches_button.grid(row=19,column=self.column+18,padx=5,pady=5)
            
            def show_final_touches_info1():
                message='''
Final touches can be made to your segmented volume to improve its appearance when viewed in 3D. These changes will not affect quantitative measurements. Final touches can only be applied after you have differentiated the elements. If you have reopened a workspace, click View elements first.

You can choose to smoothen the edges with the Smoothen ON/OFF toggle. This erodes the edges of your segmented elements. You can tune the extent of the smoothening by changing the Factor. 
Recommended values: 1-5
Avoid using a very high factor for the smoothening as it may erode away your segmented elements.

You can choose to apply a Gaussian filter to blur the edges of the segmented elements with the Gaussian filter ON/OFF toggle. This will not erode the edges of your segmented elements. You can increase the filter by increasing Sigma. 
Recommended values: 1-3

Click apply to make these changes. Images will be saved to the folder 'differentiated_elements_final_touches'.

Click View elements to change the color scheme before applying final touches.

Read more?
'''
                info_window=messagebox.askyesno(title='Final touches',message=message)
                if info_window==True:
                    show_final_touches_info2()
            
            def show_final_touches_info2():
                message='''
To view the segmented volume in 3D:

1. Open Fiji
2. File > Import > Image Sequence...
3. Select the 'differentiated_elements_final_touches' folder
4. Image > Properties...
Modify the pixel width, pixel height, and voxel depth if necessary. Change the units too.
Note, if your imported image was scaled down, you need to divide the original voxel depth by the scale factor. The scale factor can be found in the log file.
5. Plugins > 3D Viewer > Display as Volume > OK 

Go back?
'''+str(email_string)
                info_window=messagebox.askyesno(title='Final touches',message=message)
                if info_window==True:
                    show_final_touches_info1()
            
            final_touches_info_button=Button(master=self.master,text='i',width=3,command=show_final_touches_info1)
            final_touches_info_button.grid(row=19,column=self.column+20,columnspan=2,padx=5,pady=5)


            reload_window_button=Button(master=self.master,text='Reload window',command=reload_window)
            reload_window_button.grid(row=14,column=self.column+11,columnspan=2,sticky=W)

            def show_reload_window_info():
                message='''
Reload the window if it starts to become sluggish. Changes will be automatically saved to the folder 'segmented_volume'.
'''+str(email_string)
                messagebox.showinfo(title='Reload window',message=message)
            
            reload_window_info_button=Button(master=self.master,text='i',width=3,command=show_reload_window_info)
            reload_window_info_button.grid(row=14,column=self.column+20,columnspan=2,padx=5,pady=5,sticky=N+W)
            
            
            def show_limit_options():
                global limit_entry
                if smoothen_iteration_limit.get()==1:
                    limit_entry=Entry(master=self.master,width=3)
                    limit_entry.grid(row=13,column=self.column+13,sticky=W)
                    limit_entry.insert(0,'inf')
                else:
                    if limit_entry!=None:
                        limit_entry.destroy()
    
    def mini_seg_enable_draw_rectangle(self):
        self.display_image(current_z)
        SegmentedView.selection_coordinates=[]
        SegmentedView.mini_seg_threshold_selection=[]
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
        SegmentedView.segmented_vol_segmented_canvas.bind('<Button-1>',self.mini_seg_draw_rectangle)

    def mini_seg_draw_rectangle(self,event):
        if len(SegmentedView.selection_coordinates)<2:
            coord=SelectionCoordinates(x_pos=event.x,y_pos=event.y)
            SegmentedView.selection_coordinates.append(coord)

            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
            SegmentedView.segmented_vol_segmented_canvas.create_oval(event.x-1,event.y-1,event.x+1,event.y+1,fill="orange",outline='orange')
            
        if len(SegmentedView.selection_coordinates)==2:
            SegmentedView.validate_selection_coordinates()
            SegmentedView.segmented_vol_segmented_canvas=self.get_segmented_vol_canvas()
            rectangle=SegmentedView.segmented_vol_segmented_canvas.create_rectangle(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[0].y_pos,\
                SegmentedView.selection_coordinates[1].x_pos,SegmentedView.selection_coordinates[1].y_pos,outline='orange',fill='')
            SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.mini_seg_draw_threshold)
            
    def mini_seg_draw_threshold(self,event):
        if current_z==None:
            try:
                self.display_image(0)
            except:
                pass
        x_pos=event.x
        y_pos=event.y
        pixel=stack[current_z].image_array[(y_pos,x_pos)]
        mini_seg_threshold_selection=list(SegmentedView.mini_seg_threshold_selection)
        mini_seg_threshold_selection.append(pixel)
        SegmentedView.mini_seg_threshold_selection=mini_seg_threshold_selection
        lower_threshold=int(min(SegmentedView.mini_seg_threshold_selection))
        SegmentedView.mini_seg_lower_threshold_entry.delete(0,END)
        SegmentedView.mini_seg_lower_threshold_entry.insert(0,str(lower_threshold))
        upper_threshold=int(max(SegmentedView.mini_seg_threshold_selection))
        SegmentedView.mini_seg_upper_threshold_entry.delete(0,END)
        SegmentedView.mini_seg_upper_threshold_entry.insert(0,str(upper_threshold))
        
        if len(list(SegmentedView.mini_seg_threshold_selection))>=2:
            self.mini_seg_display_threshold(event)
    
    def mini_seg_display_threshold(self,event):
        lower_threshold=int(SegmentedView.mini_seg_lower_threshold_entry.get())
        upper_threshold=int(SegmentedView.mini_seg_upper_threshold_entry.get())
        max_x_pos=max(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
        min_x_pos=min(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
        max_y_pos=max(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
        min_y_pos=min(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
        for x_pos in range(min_x_pos,max_x_pos+1):
            for y_pos in range(min_y_pos,max_y_pos+1):
                if stack[current_z].image_array[(y_pos,x_pos)]>=lower_threshold:
                    if stack[current_z].image_array[(y_pos,x_pos)]<=upper_threshold:
                        SegmentedView.segmented_vol_segmented_canvas.create_rectangle(x_pos,y_pos,x_pos,y_pos,fill='green2',outline='')

    def set_lower_z(self):
        if isinstance(current_z,int):
            SegmentedView.segmented_vol_z_start_entry.delete(0,END)
            SegmentedView.segmented_vol_z_start_entry.insert(0,str(current_z))

    def set_upper_z(self):
        if isinstance(current_z,int):
            SegmentedView.segmented_vol_z_end_entry.delete(0,END)
            SegmentedView.segmented_vol_z_end_entry.insert(0,str(current_z))

    def refresh_threshold(self):
        SegmentedView.mini_seg_threshold_selection=[]
        SegmentedView.mini_seg_lower_threshold_entry.delete(0,END)
        SegmentedView.mini_seg_upper_threshold_entry.delete(0,END)
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
        self.display_image(current_z)
        if len(SegmentedView.selection_coordinates)==2:
            SegmentedView.segmented_vol_segmented_canvas=self.get_segmented_vol_canvas()
            rectangle=SegmentedView.segmented_vol_segmented_canvas.create_rectangle(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[0].y_pos,\
                SegmentedView.selection_coordinates[1].x_pos,SegmentedView.selection_coordinates[1].y_pos,outline='orange',fill='')
            SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.mini_seg_draw_threshold)

    def mini_segment(self):
        if SegmentedView.mini_seg_lower_threshold_entry.get()=='':
            return
        if SegmentedView.mini_seg_upper_threshold_entry.get()=='':
            return
        lower_threshold=int(SegmentedView.mini_seg_lower_threshold_entry.get())
        upper_threshold=int(SegmentedView.mini_seg_upper_threshold_entry.get())
        minimum_width=SegmentedView.mini_seg_minimum_width_entry.get()
        try:
            minimum_width=int(minimum_width)
            minimum_width_option=True
        except ValueError:
            minimum_width_option=False

        lower_z=int(SegmentedView.segmented_vol_z_start_entry.get())-1
        upper_z=int(SegmentedView.segmented_vol_z_end_entry.get())-1


        max_x_pos=max(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
        min_x_pos=min(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
        max_y_pos=max(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
        min_y_pos=min(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
        mini_width=int(max_x_pos-min_x_pos)+1
        mini_height=int(max_y_pos-min_y_pos)+1
        SegmentedView.selection_coordinates=[]
        
        statement='Local seg: ('+str(min_y_pos)+','+str(max_y_pos+1)+':'+str(min_x_pos)+','+str(max_x_pos)+') in z ('+str(lower_z)+':'+str(upper_z)+') Lower threshold: '+str(lower_threshold)+' Upper threshold: '+str(upper_threshold)
        if not minimum_width_option:
            statement=statement+' No min width'
        else:
            statement=statement+' Min width: '+str(minimum_width)
        LogWindow.update_log(statement)

        for z in range (lower_z,upper_z+1):
            try:
                mini_array=stack[z].image_array[min_y_pos:max_y_pos+1,min_x_pos:max_x_pos+1]
                threshold_array=np.where(mini_array<lower_threshold,-1,mini_array)
                threshold_array=np.where(threshold_array>upper_threshold,-1,threshold_array)
                threshold_array=np.where(threshold_array==-1,0,1)
                threshold_array=np.array(threshold_array,dtype=np.uint8)
                if not minimum_width_option: #just threshold; no minimum width
                    rgb_list=[]
                    for value in np.nditer(threshold_array):
                        if value==1:
                            rgb_list.append(self.RGBA)
                        elif value==0:
                            rgb_list.append((0,0,0,0))
                                  
                    modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                    count=0
                    for row in range(min_y_pos,max_y_pos+1):
                        for column in range(min_x_pos,max_x_pos+1):
                                if sum(modified_array[row,column])==0: #avoids overwrite or erase of existing segmented pixels
                                    modified_array[row,column]=rgb_list[count]
                                count+=1
                elif minimum_width_option:
                    ########### applying horizontal min width###############
                    count=0
                    for row in range(0,mini_height): 
                        for col in range(0,mini_width):
                            if threshold_array[row,col]==1:
                                count+=1
                            else:
                                if count>0: 
                                    if count<minimum_width:
                                        for col in range(col-count,col+1): #horizontal elimination
                                            threshold_array[row,col]=0
                                count=0
                    
                     ########### applying vertical min width###############
                    count=0
                    for col in range(0,mini_width): 
                        for row in range(0,mini_height):
                            if threshold_array[row,col]==1:
                                count+=1
                            else:
                                if count>0: 
                                    if count<minimum_width:
                                        for row in range(row-count,row+1): #horizontal elimination
                                            threshold_array[row,col]=0
                                count=0
                    
                    #####segments shorter than the minimum width may exist at the ends of rows and columns.

                    def remove_ends(array,number_of_rows):
                        for row in range(0,number_of_rows):
                            valid_segment=True #assume segment is valid at the start and then disprove
                            if array[0,row]!=0: #check the left most pixel of each row
                                for col in range(1,minimum_width+1): #if a pixel is segmented, check it is segmented for the minimum width
                                    if array[col,row]==0:
                                        valid_segment=False #if any pixel is 0 within the limits of the minimum width then the segment is too short
                                        break
                                
                                if valid_segment==False:
                                    for col in range(0,minimum_width+1):
                                        array[col,row]=0 #remove the invalid segment

                    horizontal_flip=np.fliplr(threshold_array) #flip horizontally to work from left to right
                    remove_ends(horizontal_flip,mini_width)
                    clockwise_rotation=np.rot90(horizontal_flip,k=-1) #rotate the array so that the ends of columns become the beginnings of rows
                    remove_ends(clockwise_rotation,mini_height)
                    reverse_rotation=np.rot90(clockwise_rotation,k=1) #reverse the rotation
                    threshold_array=np.fliplr(horizontal_flip) #reverse the horizontal flip
                    
                    
                    rgb_list=[]
                    for value in np.nditer(threshold_array):
                        if value==1:
                            rgb_list.append(self.RGBA)
                        elif value==0:
                            rgb_list.append((0,0,0,0))
                    
                    modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                    count=0
                    for row in range(min_y_pos,max_y_pos+1):
                        for column in range(min_x_pos,max_x_pos+1):
                                if sum(modified_array[row,column])==0: #avoids overwrite or erase of existing segmented pixels
                                    modified_array[row,column]=rgb_list[count]
                                count+=1
                    
                    

            except IndexError: #if at the end of the stack
                pass
        
        self.display_image(z_slice=current_z-1)
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()

    def fill_pixels_rectangle_segmented_vol(self,event):
        try:
            z_start=SegmentedView.segmented_vol_z_start_entry.get()
            z_start=int(z_start)-1
            z_end=SegmentedView.segmented_vol_z_end_entry.get()
            z_end=int(z_end)-1
        except ValueError:
            return
        if len(SegmentedView.selection_coordinates)<2:
            coord=SelectionCoordinates(x_pos=event.x,y_pos=event.y)
            SegmentedView.selection_coordinates.append(coord)

            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
            SegmentedView.segmented_vol_segmented_canvas.create_oval(event.x-1,event.y-1,event.x+1,event.y+1,fill="red",outline='red')
            
        if len(SegmentedView.selection_coordinates)==2:
            SegmentedView.segmented_vol_segmented_canvas=self.get_segmented_vol_canvas()
            rectangle=SegmentedView.segmented_vol_segmented_canvas.create_rectangle(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[0].y_pos,\
                SegmentedView.selection_coordinates[1].x_pos,SegmentedView.selection_coordinates[1].y_pos,outline='red',fill='')

            max_x_pos=max(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
            min_x_pos=min(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
            max_y_pos=max(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
            min_y_pos=min(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
            for z in range(z_start,z_end+1):
                modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                for row in range(min_y_pos,max_y_pos+1):
                    for column in range(min_x_pos,max_x_pos+1):
                            modified_array[row,column]=self.RGBA
            self.display_image(z_slice=current_z-1)
            SegmentedView.selection_coordinates=[]
            SegmentedView.segmented_vol_segmented_canvas=self.get_segmented_vol_canvas()
            SegmentedView.segmented_vol_segmented_canvas.bind('<Button-1>',self.fill_pixels_rectangle_segmented_vol)

    def enable_fill_rectangle_segmented_vol(self):
        SegmentedView.segmented_vol_segmented_canvas=self.get_segmented_vol_canvas()
        SegmentedView.segmented_vol_segmented_canvas.bind('<Button-1>',self.fill_pixels_rectangle_segmented_vol)
        SegmentedView.segmented_vol_segmented_canvas.unbind('<B1-Motion>')      

    def point_fill_pixels_segmented_vol(self,event):
        
        if SegmentedView.point_iterator<SegmentedView.point_iterator_max:
            SegmentedView.point_iterator+=1
        elif SegmentedView.point_iterator>=SegmentedView.point_iterator_max:
            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
            self.display_image(z_slice=current_z-1)
            SegmentedView.point_iterator=0

        try:
            z_start=SegmentedView.segmented_vol_z_start_entry.get()
            z_start=int(z_start)-1
            z_end=SegmentedView.segmented_vol_z_end_entry.get()
            z_end=int(z_end)-1
        except ValueError:
            return
        
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()

        for z in range(z_start,z_end+1):
                modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                try:
                    column=event.x-int(point_size/2)
                    last_column=event.x+int(point_size/2)
                    row=event.y-int(point_size/2)
                    last_row=event.y+int(point_size/2)
                    for pixel in np.nditer(point_size_list[point_size-1]):
                        if pixel==1:
                            modified_array[row,column]=segmented_vol_segmented_view.RGBA

                        if row<last_row:
                            row+=1
                        elif row==last_row:
                            row=event.y-int(9/2)
                            if column<last_column:
                                column+=1
                            elif column==last_column:
                                column=event.x-int(9/2)
                    SegmentedView.segmented_vol_segmented_canvas.create_oval(event.x-(point_size/2)-1,event.y-(point_size/2)-1,event.x+(point_size/2)+1,event.y+(point_size/2)+1,fill='#71d6f4',outline='')

                except IndexError:
                    pass
        
        
        
        SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.point_fill_pixels_segmented_vol)

    def enable_point_fill_segmented_vol(self):
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
        SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.point_fill_pixels_segmented_vol)
        SegmentedView.segmented_vol_segmented_canvas.unbind('<Button-1>')

    def point_erase_pixels_segmented_vol(self,event):

        if SegmentedView.point_iterator<SegmentedView.point_iterator_max:
            SegmentedView.point_iterator+=1
        elif SegmentedView.point_iterator>=SegmentedView.point_iterator_max:
            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
            self.display_image(z_slice=current_z-1)
            SegmentedView.point_iterator=0

        try:
            z_start=SegmentedView.segmented_vol_z_start_entry.get()
            z_start=int(z_start)-1
            z_end=SegmentedView.segmented_vol_z_end_entry.get()
            z_end=int(z_end)-1
        except ValueError:
            return
        
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()

        for z in range(z_start,z_end+1):
                modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                try:
                    column=event.x-int(point_size/2)
                    last_column=event.x+int(point_size/2)
                    row=event.y-int(point_size/2)
                    last_row=event.y+int(point_size/2)
                    for pixel in np.nditer(point_size_list[point_size-1]):
                        if pixel==1:
                            modified_array[row,column]=(0,0,0,0)

                        if row<last_row:
                            row+=1
                        elif row==last_row:
                            row=event.y-int(9/2)
                            if column<last_column:
                                column+=1
                            elif column==last_column:
                                column=event.x-int(9/2)
                    SegmentedView.segmented_vol_segmented_canvas.create_oval(event.x-(point_size/2)-1,event.y-(point_size/2)-1,event.x+(point_size/2)+1,event.y+(point_size/2)+1,fill='red',outline='')

                                
                except IndexError:
                    pass

        SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.point_erase_pixels_segmented_vol)
    
    def enable_point_erase_segmented_vol(self):
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
        SegmentedView.segmented_vol_segmented_canvas.bind('<B1-Motion>',self.point_erase_pixels_segmented_vol)
        SegmentedView.segmented_vol_segmented_canvas.unbind('<Button-1>')

    def erase_pixels_segmented_vol(self,event):
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()

        try:
            z_start=SegmentedView.segmented_vol_z_start_entry.get()
            z_start=int(z_start)-1
            z_end=SegmentedView.segmented_vol_z_end_entry.get()
            z_end=int(z_end)-1
        except ValueError:
            return
        if len(SegmentedView.selection_coordinates)<2:
            coord=SelectionCoordinates(x_pos=event.x,y_pos=event.y)
            SegmentedView.selection_coordinates.append(coord)
            SegmentedView.segmented_vol_segmented_canvas.create_oval(event.x-1,event.y-1,event.x+1,event.y+1,fill="red",outline='red')
        if len(SegmentedView.selection_coordinates)==2:
            SegmentedView.validate_selection_coordinates()
            max_x_pos=max(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
            min_x_pos=min(SegmentedView.selection_coordinates[0].x_pos,SegmentedView.selection_coordinates[1].x_pos)
            max_y_pos=max(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
            min_y_pos=min(SegmentedView.selection_coordinates[0].y_pos,SegmentedView.selection_coordinates[1].y_pos)
            if min_x_pos<=4:
                min_x_pos=0
            if min_y_pos<=4:
                min_y_pos=0
            for z in range(z_start,z_end+1):
                modified_array=SegmentedView.segmented_vol_segmented_stack[z].image_array
                for row in range(min_y_pos,max_y_pos):
                    for column in range(min_x_pos,max_x_pos):
                        try:
                            modified_array[row,column]=(0,0,0,0)
                        except IndexError:
                            pass
            self.display_image(z_slice=current_z-1)
            SegmentedView.selection_coordinates=[]
            SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
            SegmentedView.segmented_vol_segmented_canvas.bind('<Button-1>',self.erase_pixels_segmented_vol)

    def enable_erase_segmented_vol(self):
        SegmentedView.segmented_vol_segmented_canvas=SegmentedView.get_segmented_vol_canvas()
        SegmentedView.segmented_vol_segmented_canvas.bind('<Button-1>',self.erase_pixels_segmented_vol)
        SegmentedView.segmented_vol_segmented_canvas.unbind('<B1-Motion>')

    def switch_stack_segmented_vol(self):
        if SegmentedView.show_input_image:
            SegmentedView.show_input_image=False
        else:
            SegmentedView.show_input_image=True
        self.display_image(z_slice=current_z)

    def switch_layer_segmented_vol(self):
        if SegmentedView.show_segmentation:
            SegmentedView.show_segmentation=False
        else:
            SegmentedView.show_segmentation=True
        self.display_image(z_slice=current_z)







class LockPreview(object):

    lock_previews=False

    def __init__(self,source_window,target_window):
        self.source_window=source_window
        self.target_window=target_window
        self.lock_button_source_window=Button(self.source_window,text='Lock',command=self.locking_previews)
        self.lock_button_source_window.grid(row=3,column=11,padx=5,pady=5)
        self.lock_button_target_window=Button(self.target_window,text='Lock',command=self.locking_previews)
        self.lock_button_target_window.grid(row=2,column=11,padx=5,pady=5)
        self.__version=1
        
    def locking_previews(self):
        if LockPreview.lock_previews==False:
            LockPreview.lock_previews=True
            self.lock_button_source_window.config(text='Unlock')
            self.lock_button_target_window.config(text='Unlock')
        elif LockPreview.lock_previews==True:
            LockPreview.lock_previews=False
            self.lock_button_source_window.config(text='Lock')
            self.lock_button_target_window.config(text='Lock')

class PixelArray(object):
    def __init__(self,image_array):
        self.image_array=image_array
        self.__version=1 #useful to store version number if loading old workspace into new version of the software
    
    def check_version(self):
        if self.__version==1:
            pass
    
class SegmentedArray(PixelArray,Frame):

    dynamic_range_minimum=0
    dynamic_range_maximum=255
    binary_stack=[]
    horizontal_decompressed_stack=[]
    preview_option=False


    @staticmethod
    def validate_threshold_entries():
        global lower_threshold_entry_segmented_vol
        global upper_threshold_entry_segmented_vol
        try:
            lower=int(lower_threshold_entry_segmented_vol.get())
            lower_threshold_entry_segmented_vol.config({"background": "white"})
        except ValueError:
            lower_threshold_entry_segmented_vol.config({"background": "lightpink"})
            return False
        try:
            upper=int(upper_threshold_entry_segmented_vol.get())
            upper_threshold_entry_segmented_vol.config({"background": "white"})
        except ValueError:
            upper_threshold_entry_segmented_vol.config({"background": "lightpink"})
            return False
        
        if lower>upper:
            lower_threshold_entry_segmented_vol.config({"background": "lightpink"})
            upper_threshold_entry_segmented_vol.config({"background": "lightpink"})
            return False
        
        if lower<SegmentedArray.dynamic_range_minimum:
            warning_message1='The value '+str(lower)+' you entered is lower than the minimum ('+str(SegmentedArray.dynamic_range_minimum)+')'
            warning_message2='Change to minimum?'
            warning_message=warning_message1+'\n\n'+warning_message2
            change_to_minimum=messagebox.askokcancel('Invalid minimum threshold',warning_message)
            if change_to_minimum:
                lower_threshold_entry_segmented_vol.delete(0,END)
                lower_threshold_entry_segmented_vol.insert(0,str(SegmentedArray.dynamic_range_minimum))
            else:
                lower_threshold_entry_segmented_vol.delete(0,END)
                lower_threshold_entry_segmented_vol.insert(0,'NaN')
                lower_threshold_entry_segmented_vol.config({"background": "lightpink"})
                return False
        
        if upper>SegmentedArray.dynamic_range_maximum:
            warning_message1='The value '+str(upper)+' you entered is greater than the maximum ('+str(SegmentedArray.dynamic_range_maximum)+')'
            warning_message2='Change to maximum?'
            warning_message=warning_message1+'\n\n'+warning_message2
            change_to_maximum=messagebox.askokcancel('Invalid maximum threshold',warning_message)
            if change_to_maximum:
                upper_threshold_entry_segmented_vol.delete(0,END)
                upper_threshold_entry_segmented_vol.insert(0,str(SegmentedArray.dynamic_range_maximum))
            else:
                upper_threshold_entry_segmented_vol.delete(0,END)
                upper_threshold_entry_segmented_vol.insert(0,'NaN')
                upper_threshold_entry_segmented_vol.config({"background": "lightpink"})
                return False
        return True

    @staticmethod
    def set_dynamic_range(minimum,maximum):
        try:
            minimum=int(minimum)
            maximum=int(maximum)
        except ValueError:
            return
        SegmentedArray.dynamic_range_minimum=minimum
        SegmentedArray.dynamic_range_maximum=maximum

    @staticmethod
    def check_for_elements(run_length_encoded_list):
        if len(run_length_encoded_list)==0:
            warning_message1='These segmentation parameters are too harsh. No segmented elements could be produced.'
            warning_message2='Things you can try:'
            warning_message3='1. Increase the threshold range'
            warning_message4='2. Reduce the minimum width'
            warning_message5='3. Try again without a minimum width'
            warning_message=warning_message1+'\n\n'+warning_message2+'\n\n\t'+warning_message3+'\n\t'+warning_message4+'\n\t'+warning_message5
            warning_window=messagebox.showerror('Error: Harsh segmentation parameters',warning_message)
            return False
        elif len(run_length_encoded_list)==1:
            warning_message1='These segmentation parameters are too liberal. No background remains.'
            warning_message2='Things you can try:'
            warning_message3='1. Decrease the threshold range'
            warning_message4='2. Increase the minimum width'
            warning_message=warning_message1+'\n\n'+warning_message2+'\n\n\t'+warning_message3+'\n\t'+warning_message4
            warning_window=messagebox.showerror('Error: Liberal segmentation parameters',warning_message)
            return False
        else:
            return True

    

    def __init__(self,master,image_array,volume_feature,lower_threshold=0,upper_threshold=255,minimum_width=''):
        super().__init__(image_array)
        Frame.__init__(self,master) #Image module does not work without Frame superclass
        self.volume_feature=volume_feature
        self.__lower_threshold=lower_threshold
        self.__upper_threshold=upper_threshold
        self.__minimum_width=minimum_width
        self.__version=1
    
    @property
    def lower_threshold(self):
        return self.__lower_threshold
    
    @lower_threshold.setter
    def lower_threshold(self,lower_threshold):
        if SegmentedArray.validate_threshold_entries():
            self.__lower_threshold=int(lower_threshold)
        else:
            self.__lower_threshold='abort'
    
    @property
    def upper_threshold(self):
        return self.__upper_threshold
    
    @upper_threshold.setter
    def upper_threshold(self,upper_threshold):
        if SegmentedArray.validate_threshold_entries():
            self.__upper_threshold=int(upper_threshold)
        else:
            self.__upper_threshold='abort'
    
    @property
    def minimum_width(self):
        return self.__minimum_width
    
    @minimum_width.setter
    def minimum_width(self,minimum_width):
        if minimum_width.strip()=='':
            self.__minimum_width=''
        else:
            try:
                minimum_width=int(minimum_width)
            except ValueError:
                minimum_width_entry_segmented_vol.config({"background": "lightpink"})
                return
            if minimum_width>source_image_width or minimum_width>source_image_height:
                warning_message='Minimum width of '+str(minimum_width)+' is greater than image size ('+str(source_image_width)+' x '+str(source_image_height)+') in at least one dimension.'
                warning_window=messagebox.showerror('Invalid minimum width',warning_message)
                minimum_width_entry_segmented_vol.delete(0,END)
                minimum_width_entry_segmented_vol.insert(0,'')
                minimum_width_entry_segmented_vol.config({"background": "white"})
                self.__minimum_width='abort'
                return 
            else:
                self.__minimum_width=int(minimum_width)
                minimum_width_entry_segmented_vol.config({"background": "white"})

    def get_parameters(self):
        self.lower_threshold=lower_threshold_entry_segmented_vol.get()
        self.upper_threshold=upper_threshold_entry_segmented_vol.get()
        self.minimum_width=minimum_width_entry_segmented_vol.get()

        if self.lower_threshold=='abort' or self.upper_threshold=='abort' or self.minimum_width=='abort':
            return False

    def choose_segmented_vol(self):
        
        if self.get_parameters()==False:
            return
        
        skip=False
        if self.__minimum_width=='': #empty
            skip=True

        if skip:
            LogWindow.update_log('\n\n\tLower threshold: '+str(self.__lower_threshold)+'\t\tUpper threshold: '+str(self.__upper_threshold)+'\t\tNo minimum width')
            self.segment(lower_threshold=self.__lower_threshold,\
                upper_threshold=self.__upper_threshold,minimum_width=self.__minimum_width,method='THRESHOLD',\
                    raster='HORIZONTAL',color=color,next_row=0,next_column=12,label='Threshold',save=True)
            
            
            segmented_vol_segmented_view=SegmentedView('global_segmentation_by_threshold',master=segmented_vol_segmented_window,volume_feature=volume_feature,\
                RGBA=(255,0,255,100),column=1)
            LogWindow.update_log('Assembling segmentation...')
            
            segmented_vol_segmented_view.display_image(z_slice=current_z)
            segmented_vol_segmented_view.display_scroll_bar(initial=True)
            segmented_vol_segmented_view.display_stack_extremes()
            segmented_vol_segmented_view.display_stack_button()
            segmented_vol_segmented_view.display_layer_button()
            segmented_vol_segmented_view.display_edit_buttons()

        if not skip:
            LogWindow.update_log('\n\n\tLower threshold: '+str(self.__lower_threshold)+'\t\tUpper threshold: '+str(self.__upper_threshold)+'\t\t\tMinimum width: '+str(self.__minimum_width))
            self.segment(lower_threshold=self.__lower_threshold,\
                upper_threshold=self.__upper_threshold,minimum_width=self.__minimum_width,method='THRESHOLD',\
                    raster='HORIZONTAL',color=color,next_row=0,next_column=12,label='Threshold',save=True)
            self.segment(lower_threshold=self.__lower_threshold,\
                upper_threshold=self.__upper_threshold,minimum_width=self.__minimum_width,method='BY_WIDTH',\
                    raster='HORIZONTAL',color=color,next_row=1,next_column=12,label='Horizontal raster scan',save=True)
            self.segment(lower_threshold=self.__lower_threshold,\
                upper_threshold=self.__upper_threshold,minimum_width=self.__minimum_width,method='BY_WIDTH',\
                    raster='VERTICAL',color=color,next_row=2,next_column=12,label='Horizontal raster scan',save=True)
            
            
            segmented_vol_segmented_view=SegmentedView('global_segmentation_by_minimum_width',master=segmented_vol_segmented_window,volume_feature=volume_feature,\
                RGBA=(255,0,255,100),column=1)
            LogWindow.update_log('Assembling segmentation...')
            segmented_vol_segmented_view.display_image(z_slice=current_z)
            segmented_vol_segmented_view.display_scroll_bar(initial=True)
            segmented_vol_segmented_view.display_stack_extremes()
            segmented_vol_segmented_view.display_stack_button()
            segmented_vol_segmented_view.display_layer_button()
            segmented_vol_segmented_view.display_edit_buttons()
    
    def skip_global_segmentation(self):
        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory('segmented_volume',parent_directory=False)
        
        blank_array=np.zeros((source_image_width,source_image_height)).astype('uint8')
        disp_image=Image.fromarray(blank_array)
        for z in range(0,len(stack)):
            string_z_pos=StringZ.int_to_3_dec_string(z)
            disp_image.save(string_z_pos+'.tif')
        
        global segmented_vol_segmented_view
        segmented_vol_segmented_view=SegmentedView('segmented_volume',master=segmented_vol_segmented_window,volume_feature=volume_feature,\
                RGBA=(255,0,255,100),column=1)
        LogWindow.update_log('Skipping global segmentation...')
        segmented_vol_segmented_view.display_image(z_slice=current_z)
        segmented_vol_segmented_view.display_scroll_bar(initial=True)
        segmented_vol_segmented_view.display_stack_extremes()
        segmented_vol_segmented_view.display_stack_button()
        segmented_vol_segmented_view.display_layer_button()
        segmented_vol_segmented_view.display_edit_buttons()
        
            
            
        

    def segment(self,lower_threshold,upper_threshold,minimum_width,method,raster,color,next_row,next_column,label,width_filter=False,save=True):
        global stack
        os.chdir(directory_name)

        working_stack=copy.deepcopy(stack)
        z_index=0
        if method=='THRESHOLD':
            start_time=time.time()
            if save:
                Files.change_and_check_directory(workspace_filename)
                Files.change_and_overwrite_directory('global_segmentation_by_threshold',parent_directory=False)
        
            SegmentedArray.binary_stack=[]
            
            while z_index<len(working_stack):
                
                
                    raw_array=np.array(working_stack[z_index].image_array,dtype=np.uint8)
                    threshold_array=np.where(raw_array<lower_threshold,-1,raw_array)
                    threshold_array=np.where(threshold_array>upper_threshold,-1,threshold_array)

                    threshold_array=np.where(threshold_array==-1,0,1)
                    threshold_array=np.array(threshold_array,dtype=np.uint8)
                
                    if save:
                        string_z_pos=StringZ.int_to_3_dec_string(z_index)
                        disp_image=Image.fromarray(threshold_array)
                        disp_image.save(string_z_pos+'.tif')
                    SegmentedArray.binary_stack.append(threshold_array)
                    z_index=z_index+1
            end_time=time.time()
            LogWindow.update_log('Applied lower and upper thresholds: '+str(round((end_time-start_time),2))+' s')
            
        elif method.upper()=='BY_WIDTH':
            if raster.upper()=='HORIZONTAL':
                start_time=time.time()
                #run-length encoding
                compressed_stack=[]
                z_index=0
                while z_index<len(SegmentedArray.binary_stack):
                    log_window_progress_bar.create_z_progress(z_index,len(stack))
                    uncompressed_array=SegmentedArray.binary_stack[z_index]
                    initial=True
                    compressed_list=[]
                    for value in np.nditer(uncompressed_array):
                        if value==0:
                            new_value=0
                        elif value!=0:
                            new_value=1
                        if initial==True:
                            previous=new_value
                            entry=new_value
                            count=1
                            initial=False
                        else:
                            if new_value==previous:
                                count += 1
                            else:

                                ### apply minimum width 
                                if entry==1 and count<minimum_width:   
                                    entry=0
                                
                                ###
                                compressed_list.append((entry,count))
                                count=1
                                previous=new_value
                                entry=new_value
                    compressed_list.append((entry,count)) #final set of consecutive pixels
                        
                    compressed_stack.append(compressed_list)
                    z_index=z_index+1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Applied horizontal minimum width of '+str(minimum_width)+' pixels/voxels: '+str(round((end_time-start_time),2))+' s')

                index_number=0
                count=0
                for index in compressed_stack:
                    for entry in index:
                        count=count+int(entry[1])
                    assert count==(source_image_width*source_image_height)
                    count=0
                    index_number=index_number+1
                
                #Horizontal data decompression
                start_time=time.time()
                SegmentedArray.horizontal_decompressed_stack=[]
                z_log_index=0
                for compressed_list in compressed_stack:
                    count=0
                    decompressed_list=[]
                    while count<(source_image_width*source_image_height):
                        decompressed_list.append(False)
                        count += 1
                    
                    count=0
                    for entry in compressed_list:
                        if entry[0]==0:
                            count=count+int(entry[1])
                        if entry[0]!=0:
                            consecutive_number=1
                            while consecutive_number <= int(entry[1]):
                                decompressed_list[count]=True
                                count += 1
                                consecutive_number += 1
                    decompressed_array=np.array(decompressed_list).reshape(source_image_height,source_image_width)
                    binary_decompressed_array=np.where(decompressed_array==True,1,0)
                    binary_decompressed_array=np.array(binary_decompressed_array,dtype=np.uint8)
                    SegmentedArray.horizontal_decompressed_stack.append(binary_decompressed_array)
                    log_window_progress_bar.create_z_progress(z_log_index,len(stack))
                    z_log_index+=1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Decompressed horizontal data: '+str(round((end_time-start_time),2))+' s')

                
            elif raster.upper()=='VERTICAL':
                start_time=time.time()
                #run-length encoding
                compressed_stack=[]
                z_index=0
                while z_index<len(working_stack):
                    
                    uncompressed_array=SegmentedArray.binary_stack[z_index]
                    initial=True
                    compressed_list=[]
                    for value in np.nditer(uncompressed_array,order='F'): #use Fortran order to iterate through data column-wise
                        if value!=0:
                            new_value=1
                        elif value==0:
                            new_value=0
                        if initial==True:
                            previous=new_value
                            entry=new_value
                            count=1
                            initial=False
                        else:
                            if new_value==previous:
                                count += 1
                            else:

                                ### apply minimum width 
                                if entry==1 and count<minimum_width:   
                                    entry=0
                                
                                ###
                                compressed_list.append((entry,count))
                                count=1
                                previous=new_value
                                entry=new_value
                    compressed_list.append((entry,count)) #final set of consecutive pixels
                        
                    compressed_stack.append(compressed_list)
                    log_window_progress_bar.create_z_progress(z_index,len(stack))
                    z_index=z_index+1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Applied vertical minimum width of '+str(minimum_width)+' pixels/voxels: '+str(round((end_time-start_time),2))+' s')

                index_number=0
                count=0
                for index in compressed_stack:
                    for entry in index:
                        count=count+int(entry[1])
                    assert count==(source_image_height*source_image_width)
                    count=0
                    index_number=index_number+1

                #Vertical data decompression
                z_log_index=0
                start_time=time.time()
                vertical_decompressed_stack=[]
                for compressed_list in compressed_stack:
                    count=0
                    decompressed_list=[]
                    while count<(source_image_width*source_image_height):
                        decompressed_list.append(False)
                        count += 1
                    
                    count=0
                    for entry in compressed_list:
                        if entry[0]==0:
                            count=count+int(entry[1])
                        if entry[0]==1:
                            consecutive_number=1
                            while consecutive_number <= int(entry[1]):
                                decompressed_list[count]=True
                                count += 1
                                consecutive_number += 1
                    decompressed_array=np.array(decompressed_list).reshape(source_image_height,source_image_width)
                    decompressed_array=np.transpose(decompressed_array)
                    binary_decompressed_array=np.where(decompressed_array==True,1,0)
                    binary_decompressed_array=np.array(binary_decompressed_array,dtype=np.uint8)
                    vertical_decompressed_stack.append(binary_decompressed_array)
                    log_window_progress_bar.create_z_progress(z_log_index,len(stack))
                    z_log_index+=1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Decompressed vertical data: '+str(round((end_time-start_time),2))+' s')

            
                ###Find matching pixels/voxels
                start_time=time.time()
                z_index=0
                resultant_stack=[]
                while z_index < len(SegmentedArray.horizontal_decompressed_stack):
                    horizontal_array=SegmentedArray.horizontal_decompressed_stack[z_index]
                    vertical_array=vertical_decompressed_stack[z_index]
                    resultant_array=np.multiply(horizontal_array,vertical_array)
                    resultant_stack.append(resultant_array)
                    log_window_progress_bar.create_z_progress(z_index,len(stack))
                    z_index += 1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Found matching pixels/voxels: '+str(round((end_time-start_time),2))+' s')

                
                ##Filter horizontal artefacts
                start_time=time.time()
                #run-length encoding
                z_index=0
                compressed_stack=[]
                while z_index<len(resultant_stack):
                    uncompressed_array=resultant_stack[z_index]
                    initial=True
                    compressed_list=[]
                    for value in np.nditer(uncompressed_array):
                        if value!=0:
                            new_value=1
                        elif value==0:
                            new_value=0
                        if initial==True:
                            previous=new_value
                            entry=new_value
                            count=1
                            initial=False
                        else:
                            if new_value==previous:
                                count += 1
                            else:

                                ### apply minimum width 
                                if entry==1 and count<minimum_width:   
                                    entry=0
                                
                                ###
                                compressed_list.append((entry,count))
                                count=1
                                previous=new_value
                                entry=new_value
                    compressed_list.append((entry,count)) #final set of consecutive pixels
                        
                    compressed_stack.append(compressed_list)
                    log_window_progress_bar.create_z_progress(z_index,len(stack))
                    z_index=z_index+1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Filtered out horizontal artefacts: '+str(round((end_time-start_time),2))+' s')

                index_number=0
                count=0
                for index in compressed_stack:
                    for entry in index:
                        count=count+int(entry[1])
                    assert count==(source_image_width*source_image_height)
                    count=0
                    index_number=index_number+1
                
                #Horizontal data decompression
                start_time=time.time()
                horizontal_filter_stack=[]
                z_log_index=0
                for compressed_list in compressed_stack:
                    count=0
                    decompressed_list=[]
                    while count<(source_image_width*source_image_height):
                        decompressed_list.append(False)
                        count += 1
                    
                    count=0
                    for entry in compressed_list:
                        if entry[0]==False:
                            count=count+int(entry[1])
                        if entry[0]==True:
                            consecutive_number=1
                            while consecutive_number <= int(entry[1]):
                                decompressed_list[count]=True
                                count += 1
                                consecutive_number += 1
                    decompressed_array=np.array(decompressed_list).reshape(source_image_height,source_image_width)
                    binary_decompressed_array=np.where(decompressed_array==True,1,0)
                    binary_decompressed_array=np.array(binary_decompressed_array,dtype=np.uint8)
                    horizontal_filter_stack.append(decompressed_array)
                    log_window_progress_bar.create_z_progress(z_log_index,len(stack))
                    z_log_index+=1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Decompressed horizontally-filtered data: '+str(round((end_time-start_time),2))+' s')


            #filter out vertical artefacts
                
            if raster.upper()=='VERTICAL':
                start_time=time.time()
                #run-length encoding
                compressed_stack=[]
                z_index=0
                while z_index<len(working_stack):
                    uncompressed_array=horizontal_filter_stack[z_index]
                    initial=True
                    compressed_list=[]
                    for value in np.nditer(uncompressed_array,order='F'): #use Fortran order to iterate through data column-wise
                        if value!=0:
                            new_value=1
                        elif value==0:
                            new_value=0
                        if initial==True:
                            previous=new_value
                            entry=new_value
                            count=1
                            initial=False
                        else:
                            if new_value==previous:
                                count += 1
                            else:

                                ### apply minimum width 
                                if entry==1 and count<minimum_width:   
                                    entry=0
                                
                                ###
                                compressed_list.append((entry,count))
                                count=1
                                previous=new_value
                                entry=new_value
                    compressed_list.append((entry,count)) #final set of consecutive pixels
                        
                    compressed_stack.append(compressed_list)
                    log_window_progress_bar.create_z_progress(z_index,len(stack))
                    z_index=z_index+1
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Filtered out vertical artefacts: '+str(round((end_time-start_time),2))+' s')

                index_number=0
                count=0
                for index in compressed_stack:
                    for entry in index:
                        count=count+int(entry[1])
                    assert count==(source_image_height*source_image_width)
                    count=0
                    index_number=index_number+1

                #Vertical data decompression
                start_time=time.time()
                vertical_filter_stack=[]
                z_log_index=0
                for compressed_list in compressed_stack:
                    count=0
                    decompressed_list=[]
                    while count<(source_image_width*source_image_height):
                        decompressed_list.append(False)
                        count += 1
                    
                    count=0
                    for entry in compressed_list:
                        if entry[0]==False:
                            count=count+int(entry[1])
                        if entry[0]==True:
                            consecutive_number=1
                            while consecutive_number <= int(entry[1]):
                                decompressed_list[count]=True
                                count += 1
                                consecutive_number += 1
                    decompressed_array=np.array(decompressed_list).reshape(source_image_height,source_image_width)
                    binary_decompressed_array=np.where(decompressed_array==True,1,0)
                    binary_decompressed_array=np.array(binary_decompressed_array,dtype=np.uint8)
                    decompressed_array=np.transpose(binary_decompressed_array)
                    #decompressed_array=np.where(decompressed_array==True,False,True) #invert image
                    vertical_filter_stack.append(decompressed_array)
                    log_window_progress_bar.create_z_progress(z_log_index,len(stack))
                end_time=time.time()
                log_window_progress_bar.hide_z_progress()
                LogWindow.update_log('Decompressed vertically-filtered data: '+str(round((end_time-start_time),2))+' s')

                
                if save:
                    Files.change_and_check_directory(workspace_filename)
                    Files.change_and_overwrite_directory('global_segmentation_by_minimum_width',parent_directory=False)

                    z_index=0
                    for binary_decompressed_array in vertical_filter_stack:
                        string_z_pos=StringZ.int_to_3_dec_string(z_index)
                        disp_image=Image.fromarray(binary_decompressed_array)
                        disp_image.save(string_z_pos+'.tif')
                        z_index=z_index+1
        
    def preview_range(self):
        if self.volume_feature=='Segmented_Vol':
            lower_threshold=lower_threshold_entry_segmented_vol.get()
            upper_threshold=upper_threshold_entry_segmented_vol.get()
        
        try:
            lower_threshold=int(lower_threshold)
            upper_threshold=int(upper_threshold)
        except ValueError:
            pass
        
        if isinstance(lower_threshold,int) and isinstance(upper_threshold,int):
            row_index=0
            height_list=[]

            while row_index<source_image_height:
                if row_index % 2 ==0: #to speed things up, only work with even rows
                    column_index=0
                    width_list=[]

                    while column_index<source_image_width:
                        if column_index % 2 == 0: #only even columns
                            pixel_value=get_pixel_value(self.image_array,None,row_index,column_index)
                            adjusted_value=apply_threshold_to_pixel(pixel_value,lower_threshold,upper_threshold)
                            if adjusted_value:
                                if PreviewWindow.right_preview!=None:
                                    PreviewWindow.right_preview.create_rectangle(column_index,row_index,column_index+2,row_index+2,fill=color,outline='')
                        column_index=column_index+1
                row_index=row_index+1

    def preview_threshold(self):
        self.get_parameters()
        lower_array=np.where(self.image_array>=self.lower_threshold,1,0)
        upper_array=np.where(self.image_array<=self.upper_threshold,1,0)
        threshold_array=lower_array*upper_array
        threshold_array=np.where(threshold_array==1,0,1) #invert
        threshold_array=np.array(threshold_array,dtype=np.uint8)
        threshold_array=threshold_array*self.image_array
        new_image=Image.fromarray(threshold_array)
        render=ImageTk.PhotoImage(new_image)
        img=Label(self,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
        img.image=render #.image is a method attribute of Label
        PreviewWindow.right_preview.create_image(source_image_width/2,source_image_height/2,image=render)

    def enable_preview(self):
        if SegmentedArray.preview_option==False:
            SegmentedArray.preview_option=True
            preview_button.config(relief='sunken')
            self.view_preview()
            
        elif SegmentedArray.preview_option==True:
            SegmentedArray.preview_option=False
            preview_button.config(relief='raised')
            self.view_preview()

    def view_preview(self):
        if SegmentedArray.preview_option:
            self.preview_threshold()
        else:
            new_image=Image.fromarray(self.image_array)
            render=ImageTk.PhotoImage(new_image)
            img=Label(self,image=render) #need to assign it to a Label so that you can specify its grid coordinates below.
            img.image=render #.image is a method attribute of Label
            PreviewWindow.right_preview=Canvas(self.master,width=source_image_width,height=source_image_height)
            PreviewWindow.right_preview.grid(row=1,column=1,columnspan=9,padx=5,pady=5,sticky=N+S+E+W)
            PreviewWindow.right_preview.create_image(source_image_width/2,source_image_height/2,image=render)

class Histogram(object):

    histogram_height=75

    @staticmethod
    def display_blank_histogram(master=None):
        global histogram
        histogram=Canvas(master,width=source_image_width,height=Histogram.histogram_height,bg='black')
        histogram.grid(row=4,column=1,columnspan=9,padx=5,pady=5)
        histogram.bind('<Motion>',Histogram.show_intensity_when_scrolling)
    
    @staticmethod
    def display_histogram_limits(master=None):
        lowest_intensity_limit=Label(master,text='0')
        highest_intensity_limit=Label(master,text='255')
        lowest_intensity_limit.grid(row=4,column=0,padx=2,pady=2,sticky=E+S)
        highest_intensity_limit.grid(row=4,column=10,padx=2,pady=2,sticky=W+S)
        
    
    @staticmethod
    def show_intensity_when_scrolling(event):
        global scroll_line
        global scroll_position
        push=0
        try:
            if scroll_line is not None:
                histogram.delete(scroll_line)
                histogram.delete(scroll_position)
        except:
            pass

        scroll_line=histogram.create_rectangle(event.x-1,0,event.x+1,Histogram.histogram_height+10,fill='gray',outline='') #+10 for vertical padding
        scroll_number=str(int(((event.x-1)/source_image_width)*255))
        if int(scroll_number)<=4:
            push=6
        elif int(scroll_number)>=231:
            push=-14
        scroll_position=histogram.create_text(event.x+push,event.y-10,text=scroll_number,fill='white')
        try:
            rangegram.bind('<Motion>',rangegram_data.select_boundary)
        except AttributeError:
            pass #rangegram_data initially a tuple without the select_boundary() method attribute of the Rangegram class




    def __init__(self,volume_feature,color,order,pixel_list,master=None):
        self.master=master
        self.volume_feature=volume_feature
        self.color=color
        self.order=order
        self.pixel_list=pixel_list
        self.__version=1
    
    def transmute_pixel_list(self):
        absolute_pixel_intensity_frequency_list=[]
        for pixel_intensity in range (0,256):
            absolute_frequency=0
            index=0
            while index<len(self.pixel_list):
                if self.pixel_list[index]==pixel_intensity:
                    absolute_frequency=absolute_frequency+1
                index=index+1
            absolute_pixel_intensity_frequency_list.append(absolute_frequency)
        
        mode_frequency=max(absolute_pixel_intensity_frequency_list)
        if mode_frequency!=0:
            relative_pixel_intensity_frequency_list=[]
            for pixel_intensity in absolute_pixel_intensity_frequency_list:
                relative_frequency=int((pixel_intensity/mode_frequency)*Histogram.histogram_height)
                relative_pixel_intensity_frequency_list.append(relative_frequency)
            return relative_pixel_intensity_frequency_list
        return None


    def display_histogram(self):
        global histogram
        histogram=Canvas(self.master,width=source_image_width,height=Histogram.histogram_height,bg='black')
        histogram.grid(row=4,column=1,columnspan=9)
        histogram.bind('<Motion>',Histogram.show_intensity_when_scrolling)
    
    def update_histogram(self):
        
        relative_pixel_frequencies=Histogram.transmute_pixel_list(self)
        if relative_pixel_frequencies!=None:
            intensity_value=0
            while intensity_value<256:
                relative_intensity=relative_pixel_frequencies[intensity_value]
                if relative_intensity!=0:
                    scaled_intensity=((intensity_value+1)/256)*source_image_width
                    upper_left_x=scaled_intensity
                    upper_left_y=Histogram.histogram_height-relative_intensity
                    lower_right_x=scaled_intensity
                    lower_right_y=Histogram.histogram_height+10 #+10 for padding
                    histogram.create_rectangle(upper_left_x+1,upper_left_y,lower_right_x+3,lower_right_y,fill=self.color,outline='')
                intensity_value=intensity_value+1
        histogram.bind('<Motion>',Histogram.show_intensity_when_scrolling)
    
class Rangegram(Histogram):
    
    rangegram_handle=None
    borderwidth=3
    index_boundaries=None

    
    @staticmethod
    def display_blank_rangegram(master=None):
        global rangegram
        rangegram=Canvas(master,width=source_image_width,height=Histogram.histogram_height,bg='black')
        rangegram.grid(row=3,column=1,columnspan=9,padx=5,pady=5)
        rangegram.bind('<Motion>',Histogram.show_intensity_when_scrolling)
    
    @staticmethod
    def display_rangegram_limits(master=None):
        lowest_intensity_limit=Label(master,text='0')
        highest_intensity_limit=Label(master,text='255')
        lowest_intensity_limit.grid(row=3,column=0,padx=2,pady=2,sticky=E+S)
        highest_intensity_limit.grid(row=3,column=10,padx=2,pady=2,sticky=W+S)
    
    def __init__(self,pixel_list,master=None):
        self.pixel_list=pixel_list
        self.master=master
        self.__version=1
    
    def calculate_boundaries(self):
        if len(self.pixel_list)>0: #if pixels have been sampled
            lower=((min(self.pixel_list)+1)/256)*source_image_width #find minimum pixel value
            upper=((max(self.pixel_list)+1)/256)*source_image_width #find maximum pixel value
            return (lower,upper) #return both as a tuple
        else:
            return (None,None) #return None if pixels have not been sampled
    
    def display_rectangle(self,canvas):
        lower=None
        upper=None

        def calculate_boundaries():
            nonlocal lower
            nonlocal upper
            if len(self.pixel_list)>0: #if pixels have been sampled
                lower=((min(self.pixel_list)+1)/256)*source_image_width+1
                upper=((max(self.pixel_list)+1)/256)*source_image_width+1
                return lower,upper
            else:
                return None,None

        try:
            canvas.delete(Rangegram.index_boundaries)
        except:
            pass
        lower,upper=calculate_boundaries()
        Rangegram.index_boundaries=canvas.create_rectangle(lower,1,upper,Histogram.histogram_height+10,fill='',outline='magenta',width=Rangegram.borderwidth)
    
    def select_boundary(self,event):
        if Rangegram.rangegram_handle!=None: #global variable
            rangegram.delete(Rangegram.rangegram_handle) #delete rangegram_handle before redraw
        
        def draw_handle(self):
            end_function=False #condition for repeating the function. 
            #If the mouse is not within reach of the boundaries, end_function == False and the function should repeat.
            #If the mouse is within reach of the boundaries, end_function == True and the handlebar will be drawn without repeating the function.
            
            lower=rangegram_data.calculate_boundaries()[0] 
            upper=rangegram_data.calculate_boundaries()[1] #get the lower and upper boundaries

            lower_get=lower_threshold_entry_segmented_vol #the entry field for the lower value
            upper_get=upper_threshold_entry_segmented_vol #the entry field for the upper value


            def move_boundary(event):
                nonlocal left_boundary
                nonlocal lower_get
                nonlocal upper_get
                global rangegram_data
                if Rangegram.rangegram_handle!=None:
                    rangegram.delete(Rangegram.rangegram_handle)
                if left_boundary: #if the mouse event is within reach of the left boundary
                    if int(lower_get.get())<int(event.x): #if mouse event is lower than the lower entry value
                        new_entry=int((event.x/source_image_width)*256) #create a new lower entry
                        if new_entry>=0 and new_entry<=255: #ensure entry is within limits of dynamic range
                            rangegram_data.pixel_list.append(new_entry) #append it to the pixel_list so the boundary will change
                            lower_get.delete(0,END)
                            lower_get.insert(0,new_entry)
                    elif int(lower_get.get())>int(event.x): #if mouse event is greater than the lower entry value
                        new_entry=int((event.x/source_image_width)*256) #create a new lower entry
                        if new_entry>=0 and new_entry<=255: #ensure entry is within limits of dynamic range
                            rangegram_data.pixel_list.append(new_entry) #append it to the pixel_list so the boundary will change
                            lower_get.delete(0,END)
                            lower_get.insert(0,new_entry)
                elif not left_boundary: #if the mouse event is not within reach of the left boundary (and within reach of the right boundary)
                    if int(upper_get.get())<int(event.x): #if the mouse event is lower than the upper entry value
                        new_entry=int((event.x/source_image_width)*256) #create a new upper entry
                        if new_entry>=0 and new_entry<=255: #ensure entry is within limits of dynamic range
                            rangegram_data.pixel_list.append(new_entry) #append it to the pixel_list so the boundary will change
                            upper_get.delete(0,END)
                            upper_get.insert(0,new_entry)
                    elif int(upper_get.get())>int(event.x): #if the mouse event is greater than the upper entry value
                        new_entry=int((event.x/source_image_width)*256) #create a new upper entry
                        if new_entry>=0 and new_entry<=255: #ensure entry is within limits of dynamic range
                            rangegram_data.pixel_list.append(new_entry) #append it to the pixel_list so the boundary will change
                            upper_get.delete(0,END)
                            upper_get.insert(0,new_entry)

                        
                rangegram_data.pixel_list=shrink_list(rangegram_data.pixel_list,lower=int(lower_get.get()),upper=int(upper_get.get()))
                rangegram_data.display_rectangle(rangegram)
                Rangegram.rangegram_handle=rangegram.create_rectangle(event.x-3,event.y-9,event.x+6,event.y+9,fill='magenta',outline='')
                PreviewWindow.preview_array=SegmentedArray(image_array=stack[current_z].image_array, master=preview_window,volume_feature=volume_feature,lower_threshold=None,upper_threshold=None,minimum_width=0)
                PreviewWindow.preview_array.view_preview()
                    

            if event.x>lower-5 and event.x<lower+5: #if mouse event is within reach of the lower boundary
                Rangegram.rangegram_handle=rangegram.create_rectangle(lower-3,event.y-9,lower+6,event.y+9,fill='magenta',outline='')
                end_function=True #no need to repeat the drawing function
                left_boundary=True #condition for left boundary functions
                rangegram.bind('<B1-Motion>',move_boundary)
            elif event.x>upper-5 and event.x<upper+5: #if mouse event is within reach of the upper boundary
                Rangegram.rangegram_handle=rangegram.create_rectangle(upper-3,event.y-9,upper+6,event.y+9,fill='magenta',outline='')
                end_function=True #no need to repeat the drawing function
                left_boundary=False #condition for right boundary functions
                rangegram.bind('<B1-Motion>',move_boundary)
            else:
                rangegram.unbind('<B1-Motion>') #unbinding means it doesn't matter if end_function remains True or False
                
            rangegram.bind('<Motion>',Histogram.show_intensity_when_scrolling)
            return end_function

        end_function=draw_handle(Rangegram.index_boundaries)
        if end_function==True:
            return
 
class SegmentationButtons(object):

    lower_threshold_entry_segmented_vol=None
    upper_threshold_entry_segmented_vol=None
    minimum_width_entry_segmented_vol=None


    def __init__(self,volume_feature,color,order,master):
        self.volume_feature=volume_feature
        self.color=color
        self.order=order
        self.master=master
        self.__version=1
    
    def check_version(self):
        if self.__version==1:
            pass
    
    
    def display_headers(self):
        dropper_label=Label(master=self.master,text='Eye dropper')
        dropper_label.grid(row=0,column=2,padx=5,pady=20)
        pixel_range_label=Label(master=self.master,text='Threshold  ')
        pixel_range_label.grid(row=0,column=4,padx=5,pady=5,columnspan=4)
        minimum_width_label=Label(master=self.master,text='Minimum width')
        minimum_width_label.grid(row=0,column=8,padx=5,pady=20)
        selection_label=Label(master=self.master,text='Selection')
        selection_label.grid(row=0,column=9,padx=5,pady=20)
    
    def display_buttons(self,lower=None,upper=None):
        dropper_button=Button(master=self.master,text='Eye dropper',command=self.select_volume_feature_for_dropper)
        dropper_button.grid(row=1,column=1,padx=5,pady=1)

        if self.volume_feature=='Segmented_Vol':
            pixel_range_label=Label(master=self.master,text='Threshold  ')
            pixel_range_label.grid(row=0,column=3,padx=5,pady=1)
            global lower_threshold_entry_segmented_vol
            global upper_threshold_entry_segmented_vol
            lower_threshold_entry_segmented_vol=Entry(master=self.master,width=3)
            lower_threshold_entry_segmented_vol.grid(row=1,column=2,sticky=E,padx=1,pady=1)
            if lower!=None:
                lower_threshold_entry_segmented_vol.delete(0,END)
                lower_threshold_entry_segmented_vol.insert(0,int(lower))

            colon_label=Label(master=self.master,text=':')
            colon_label.grid(row=1,column=3,padx=5,pady=1)

            upper_threshold_entry_segmented_vol=Entry(master=self.master,width=3)
            upper_threshold_entry_segmented_vol.grid(row=1,column=4,sticky=W,padx=1,pady=1)
            if upper!=None:
                upper_threshold_entry_segmented_vol.delete(0,END)
                upper_threshold_entry_segmented_vol.insert(0,int(upper))
            
            minimum_width_label=Label(master=self.master,text='Minimum width')
            minimum_width_label.grid(row=1,column=5,padx=5,pady=1)
            global minimum_width_entry_segmented_vol
            minimum_width_entry_segmented_vol=Entry(master=self.master,width=3)
            minimum_width_entry_segmented_vol.grid(row=1,column=6,padx=5,pady=1)
            segment_button=Button(master=self.master,text='Segment',background=self.color,command=the_segment.choose_segmented_vol)
            segment_button.grid(row=1,column=7,sticky=E,padx=5,pady=1)
            skip_global_segmentation_button=Button(master=self.master,text='Skip',background=self.color,command=the_segment.skip_global_segmentation)
            skip_global_segmentation_button.grid(row=1,column=11,sticky=E,padx=5,pady=1)

            def show_global_segmentation_info1():
                message='''
These windows allows you to segment the entire stack and preview the outcome. The segmentation algorithm is based on a threshold range and a minimum width restriction.

To select a threshold range in the Imported Image window, click on Eye dropper and then mouse-click and press down on features in the imported image you want to segment. Move the cursor while pressing down to pick up more pixels and expand the range.
In the Preview Segmentation window, click on Preview to inspect the threshold range. Pixels within this range will turn black. You can inspect the segmentation in different Z planes by scrolling through the Z stack with the blue bar.
Click Lock to lock the images in the two windows so that you can scroll through the Z stack in both simultaneously.
The range can be viewed in the histogram at the bottom of the Imported Image window and the boundaries of the range can be altered using the bars at the bottom of the Preview Segmentation window. The range can also be manually altered in the entry boxes.

Read more?
'''
                info_window=messagebox.askyesno(title='Global segmentation',message=message)
                if info_window==True:
                    show_global_segmentation_info2()

            
            def show_global_segmentation_info2():
                message='''
Optional: The minimum width restriction can reduce the noise picked up during the segmentation. For example, if you set the minimum width to 5 pixels, pixels within the threshold range will only be included in the segmented volume if they form part of a run of at least 5 consecutive pixels horizontally and vertically.
In other words, only matrices greater than or equal to 5x5 pixels would be included in the segmented volume. This can eliminate smaller noise. Adding a minimum width restriction does not change the preview of the segmentation. Recommended minimum width: 3-10

Tip: If your imported image is very busy and too many undesired elements are picked up using the global segmentation, it might be easier to skip the global segmentation. Click Skip and a new window will open with a blank segmented volume. You will then be able to locally-segment desired features instead.

Go back?
'''+str(email_string)
                info_window=messagebox.askyesno(title='Global segmentation',message=message)
                if info_window==True:
                    show_global_segmentation_info1()

            global_segmentation_info_button=Button(master=self.master,text='i',width=3,command=show_global_segmentation_info1)
            global_segmentation_info_button.grid(row=1,column=12,padx=5,pady=5,sticky=N+W)

    
    def select_volume_feature_for_dropper(self):
        global volume_feature
        volume_feature=self.volume_feature
        global color
        color=self.color

class SelectionCoordinates(object):

    point_size=4

    def __init__(self,x_pos,y_pos):
        self.x_pos=x_pos
        self.y_pos=y_pos
        self.upper_left=x_pos-SelectionCoordinates.point_size
        self.upper_right=y_pos-SelectionCoordinates.point_size
        self.lower_left=x_pos+SelectionCoordinates.point_size
        self.lower_right=y_pos+SelectionCoordinates.point_size
        self.__version=1

class LogWindow(Frame):

    log_width=80
    log_height=10
    bar_width=720
    bar_height=15
    z_progress_bg=None

    @staticmethod
    def create_log():
        global log_box
        log_box=Listbox(log_window)
        log_box.grid(row=1,column=1,padx=5,pady=5)
        log_box.configure(width=LogWindow.log_width,height=LogWindow.log_height)
        #log_window.withdraw() #hide when empty

    @staticmethod
    def update_log(statement):
        #log_window.deiconify()
        global log_box
        def real_time_update():
            nonlocal statement
            logger.info(statement)
            log_box.insert(END,statement)
            log_box.see(log_box.size()-1)
            log_window.update()
            log_window.after(5)  # Pause 5 millisecs.
        real_time_update()

    def __init__(self,master):
        self.master=master
        self.__version=1

    def create_z_progress(self,z_position,stack_depth):
        z_position=z_position+1
        LogWindow.z_progress_bg=Canvas(master=self.master,width=LogWindow.bar_width,height=LogWindow.bar_height,bg='gray89')
        LogWindow.z_progress_bg.grid(row=0,column=1,padx=5,pady=5)
        bar_length=(z_position/stack_depth)*LogWindow.bar_width
        z_progress_fg=LogWindow.z_progress_bg.create_rectangle(0,0,bar_length,LogWindow.bar_height+5,fill='gray64',outline='')
        bar_label=str(z_position)+' / '+str(stack_depth)
        z_progress_label=LogWindow.z_progress_bg.create_text((LogWindow.bar_width/2),10,text=bar_label,fill='black')
        log_window.update()
        log_window.after(5)  # Pause 5 millisecs.
    
    def hide_z_progress(self):
        if LogWindow.z_progress_bg!=None:
            LogWindow.z_progress_bg.delete('all')
            log_window.update()
            log_window.after(5)  # Pause 5 millisecs.

class Grouping(object):

    product_array_direction='N'
    color_index=[]
    endloop_controller=10
    alarming_slices=[]
    
    def __init__(self,segmented_stack):
        self.segmented_stack=segmented_stack
        self.grouping_of_stack=[]
        self.group_information=[]
        self.colored_stack=[]
        self.final_touches_stack=[]
        self.smoothened_grouped_stack=[]
        self.width_coordinates=[]
        self.__version=1

    def group_by_arrays(self):
        LogWindow.update_log('Grouping...')

        new_folder='differentiated_elements' #designated directory
        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory(new_folder,parent_directory=False)    
        


        #####Create number array#####
        start=time.time()
        quadrants_per_row=math.ceil(source_image_width/2) #determine the number of quadrants to have per row and round up for non-integers
        quadrants_per_col=math.ceil(source_image_height/2) #determine the number of quadrants per column and round up for non-integers
        initial_number=1 #the number given to the first quadrant in each row
        row_number=1 #the number of quadrant rows we are on, indexing from 1
        quadrant_array_as_list=[] #use an empty list because can't create and append to an empty array
        while row_number<=quadrants_per_col: #while the number of quadrant rows is no more than the max number that can fit into the image height
            row=np.arange(initial_number,initial_number+quadrants_per_row) #create positive integer values for each quadrant
            duplicated_row=np.repeat(row,2) #duplicate each value to create rows for each quadrant
            if (source_image_width % 2) !=0: #if the width is an odd number of pixels there will be a non-zero remainder
                duplicated_row=np.delete(duplicated_row,-1) #remove the last value only
            assert duplicated_row.size==source_image_width 
            quadrant_array_as_list.append(duplicated_row) #append top row of quadrants
            quadrant_array_as_list.append(duplicated_row) #append bottom row of quadrants
            initial_number=(row[-1])+1 #The last quadrant number in this row +1 is the first quadrant number in the next row
            row_number+=1 #create next row of quadrants
        quadrant_array=np.array(quadrant_array_as_list) #convert into 2D array
        if (source_image_height % 2) !=0: #if the height is an odd number of pixels there will be a non-zero remainder
            quadrant_array=np.delete(quadrant_array,obj=-1,axis=0) #delete the last row
        assert quadrant_array.shape==(source_image_width,source_image_height)
        end=time.time()
        LogWindow.update_log('Created number array: '+str(round((end-start),2))+' s')    
        
        image=Image.fromarray(quadrant_array.astype('uint32'))
        #image.save('number_array.tif')

        ####Multiply array to get initial groups####

        bool_stack=self.convert_RGBA_to_bool() #the segmented stack has shape (source_image_width, source_image_height, 4) because it is stored as RGBA. 
        #Convert to bool to get shape (source_image_width, source_image_height)
        

        def get_shifted_array(input_array,direction):
            
            def shift_array(input_array,direction):
                if direction=='S': #shift array south/downward
                    output_array=np.insert(input_array,obj=0,values=0,axis=0) #insert row of zeros at the top to shift array down
                    output_array=np.delete(output_array,obj=-1,axis=0) #delete last row to maintain dimensions
                elif direction=='N': #shift array north/upward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=0) #insert row of zeros at the bottom to shift array up
                    output_array=np.delete(output_array,obj=0,axis=0) #delete first row to maintain dimensions
                elif direction=='E': #shift array west/leftward
                    output_array=np.insert(input_array,obj=0,values=0,axis=1) #insert col of zeros on the left to shift array right
                    output_array=np.delete(output_array,obj=-1,axis=1) #delete right-most col to maintain dimensions
                elif direction=='W': #shift array west/leftward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=1) #insert col of zeros on the right to shift array left
                    output_array=np.delete(output_array,obj=0,axis=1) #delete left-most col to maintain dimensions
                return output_array
            
            if direction=='NW':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'W')
            elif direction=='NE':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'E')
            elif direction=='SW':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'W')
            elif direction=='SE':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'E')
            else:
                output_array=shift_array(input_array,direction)
            return output_array
            
        def alternate_directions():
            directions=['N','NE','E','SE','S','SW','W','NW','N'] #not made into a class attribute because it needs to be regenerated each iteration
            i=0
            while i<8:
                if Grouping.product_array_direction==directions[i]:
                    directions.remove(directions[i])
                    random.shuffle(directions)
                    Grouping.product_array_direction=directions[i]
                    return
                i+=1
        

        def multiply_arrays(working_array,shifted_array):
            multiplied_array=working_array*shifted_array
            resultant_array=np.where(multiplied_array!=working_array**2,shifted_array,working_array)
            resultant_array=np.where(shifted_array==0,working_array,resultant_array)
            return resultant_array

        def find_largest_groups(array,max_number_of_groups=10):
            start=time.time()
            group_list=set(array.flatten())#flatten method attribute converts array into single dimension and set picks out each number only once
            group_list.remove(0) #get rid of background, will usually be the largest group
            group_dictionary={}
            for group in group_list:
                all_coordinates=np.argwhere(array==group)
                group_size=all_coordinates.size
                group_dictionary[group]=group_size
            sorted_group_list=sorted(group_dictionary.items(),key=lambda x: x[1],reverse=False) #sorted will turn dictionary into list
            shortlisted_groups=sorted_group_list[0:max_number_of_groups-1]
            end=time.time()
            #LogWindow.update_log('Prioritised groups:',end-start,'s')
            return shortlisted_groups
        
        def find_neighboring_groups(source_array,group_number,direction):
            arg_working_array=np.argwhere(source_array==group_number)
            if arg_working_array.size==0:
                return None
            if direction=='W':
                shifted_values=arg_working_array[:,1]-1
                constant_values=arg_working_array[:,0]
                arg_shifted_array=np.array(list(zip(constant_values,shifted_values)))
            elif direction=='E':
                shifted_values=arg_working_array[:,1]+1
                constant_values=arg_working_array[:,0]
                arg_shifted_array=np.array(list(zip(constant_values,shifted_values)))
            elif direction=='N':
                shifted_values=arg_working_array[:,0]-1
                constant_values=arg_working_array[:,1]
                arg_shifted_array=np.array(list(zip(shifted_values,constant_values)))
            elif direction=='S':
                shifted_values=arg_working_array[:,0]+1
                constant_values=arg_working_array[:,1]
                arg_shifted_array=np.array(list(zip(shifted_values,constant_values)))
            shifted_list=[]
            for x,y in arg_shifted_array:
                try:
                    shifted_list.append(source_array[x,y])
                except IndexError:
                    pass
            shifted_array_set=set(shifted_list)
            if 0 in shifted_array_set:
                shifted_array_set.remove(0)
            if len(shifted_array_set)>1: #if there is more than one group (i.e. background wasn't the only extra element)
                return shifted_array_set
            else:
                return None
        
        def replace_neighboring_groups(source_array,desired_group,undesired_group):
            output_array=np.where(source_array==undesired_group,desired_group,source_array)
            return output_array
        
        def converge_groups(source_array,largest_groups,convergence_iterations): #iterations is the last number of the saved file e.g. 50.tif
            start=time.time()
            directions=['N','S','E','W']
            for definition in largest_groups:
                desired_group_number=definition[0]
                i=0
                while i<convergence_iterations:
                        
                    direction=random.choice(directions)
                    undesired_groups=find_neighboring_groups(source_array,desired_group_number,direction)
                    if undesired_groups != None:
                        for undesired_group in undesired_groups:
                            source_array=replace_neighboring_groups(source_array,desired_group_number,undesired_group)
                    i+=1
            end=time.time()
            #LogWindow.update_log('Converged arrays:',end-start,'s')
            return source_array


        def spiral_the_array(input_array,iterations,rotation_interval=0): #rotation_interval disabled by default
            working_array=input_array
            start=time.time()
            x=1
            while x<=iterations:
                shifted_array=get_shifted_array(working_array,direction=Grouping.product_array_direction)
                if x==rotation_interval:
                    shifted_array=np.rot90(shifted_array,1,axes=(1,0))
                    working_array=np.rot90(working_array,1,axes=(1,0))
                ###
                resultant_array=multiply_arrays(working_array=working_array,shifted_array=shifted_array)
                working_array=resultant_array
                ###
                if x==rotation_interval:
                    resultant_array=np.rot90(resultant_array,1,axes=(0,1))
                #image=Image.fromarray(resultant_array.astype('uint32'))
                #image.save(str(x)+'.tif')
                alternate_directions()
                x+=1

            end=time.time()
            #LogWindow.update_log('Spiralled arrays:',end-start,'s')
            return resultant_array
        
        def check_number_of_groups(input_array):
            individual_groups= set(input_array.flatten())
            if 0 in individual_groups:
                individual_groups.remove(0)
            number_of_groups=len(individual_groups)
            return number_of_groups
        
        def confirm_no_adjacent_groups(input_array):
            working_array=input_array
            directions=['N','NE','E','SE','S','SW','W','NW','N']

            for direction in directions:
                working_array=input_array
                shifted_array=get_shifted_array(working_array,direction=direction)
                product_array=working_array*shifted_array #background will multiply to 0. Matching group numbers will produce squares and adjacent groups will produce different positive integers.
                product_array_background_minus_1=np.where(product_array==0,-1,product_array) #make all background -1 because 0 is 0**2 and would be included alongside group pixels
                group_pixels=np.argwhere(product_array_background_minus_1==working_array**2) #only group pixels that are not at the edges or in contact with a different group
                not_background_pixels=np.argwhere(product_array!=0) #should be the same size as group pixels array
                background_pixels=np.argwhere(product_array==0) 
                assert int((background_pixels.size/2)+(not_background_pixels.size/2))==product_array.size
                if group_pixels.size!=not_background_pixels.size: #will not be equal if adjacent groups are present but only for some of the directions
                    
                    return False
   
            return True #if only 0s and squares are present and there are no adjacent groups after checking all directions


        
        def group_xy(input_array,spiral_iterations=25,convergence_iterations=25,max_number_of_groups=25):
            working_array=input_array
            i=0
            while i < 10:
                spiralled_array=spiral_the_array(working_array,spiral_iterations)
                largest_groups=find_largest_groups(spiralled_array,max_number_of_groups)
                converged_array=converge_groups(spiralled_array,largest_groups,convergence_iterations)
                #image=Image.fromarray(converged_array.astype('uint32'))
                #image.save(str(i)+'.tif')
                working_array=converged_array
                group_number=check_number_of_groups(working_array)
                LogWindow.update_log('NUMBER OF ELEMENTS:'+str(group_number))
                if i!=0:
                    if group_number==previous_number:
                        break
                previous_number=group_number
                i+=1
            return working_array


        
        def modify_groups_in_tandem_slices(lower_slice, upper_slice):
            individual_groups=set(lower_slice.flatten())
            if 0 in individual_groups:
                individual_groups.remove(0)
            
            binary_upper_array=np.where(upper_slice!=0,1,0)
            for group_number in individual_groups:
                upper_slice=np.where(lower_slice==group_number,group_number,upper_slice)
                upper_slice=upper_slice*binary_upper_array
            
            return upper_slice

        def merge_groups_in_tandem_slices(lower_slice,upper_slice):
            groups_in_lower_slice=set(lower_slice.flatten())
            if 0 in groups_in_lower_slice:
                groups_in_lower_slice.remove(0)
            
            for group_number in groups_in_lower_slice:
                coordinates=np.argwhere(lower_slice==group_number)
                for x,y in coordinates:
                    if upper_slice[x,y]!=0:
                        if upper_slice[x,y]!=group_number:
                            upper_slice=np.where(upper_slice==upper_slice[x,y],group_number,upper_slice)
                            
            
            return upper_slice

        start=time.time()
        for z in range (0,len(stack)):
            LogWindow.update_log('STARTING SLICE '+str(z+1))
            product_array=bool_stack[z].image_array*quadrant_array 
            #Background (zero/False) multiplied by quadrant numbers will become zero
            #Segmented pixels (one/True) multiplied by quadrant numbers will become quadrant numbers
            #####
            if z!=0:
                product_array=modify_groups_in_tandem_slices(lower_slice=working_array,upper_slice=product_array)
            #####
            working_array=group_xy(product_array)
            keep_iterating=True
            endloop_iterator=0
            previous_number=0
            spiral_iterations=25
            #keep grouping xy until you only get isolated groups
            while keep_iterating:
                if confirm_no_adjacent_groups(working_array): #if only isolated groups and background present
                    keep_iterating=False #end loop
                else:
                    if endloop_iterator>=Grouping.endloop_controller:
                        keep_iterating=False
                        Grouping.alarming_slices.append(z)
                        break
                    number_of_groups=check_number_of_groups(working_array)
                    if number_of_groups==previous_number:
                        endloop_iterator+=1 #if the group number isn't changing don't continue looping through after given number of attempts
                        spiral_iterations+=25
                    else:
                        spiral_iterations=25
                    previous_number=number_of_groups

                    working_array=group_xy(working_array,spiral_iterations=spiral_iterations) #keep going 
            self.grouping_of_stack.append(working_array)
            image=Image.fromarray(working_array.astype('uint32'))
            image.save(str(z)+'.tif')
        if len(Grouping.alarming_slices)>0:
            LogWindow.update_log('ALARMING SLICES:'+str(Grouping.alarming_slices))
        
        end=time.time()
        LogWindow.update_log('2D GROUPING TIME:'+str(round((end-start),2))+' s')
        
        start=time.time()
        for z in range(0,len(stack)):
            if z>0:
                LogWindow.update_log('Z GROUPING SLICES '+str(z)+' and '+str(z+1))
                self.grouping_of_stack[z]=merge_groups_in_tandem_slices(lower_slice=self.grouping_of_stack[z-1],upper_slice=self.grouping_of_stack[z])
        
        for z in range (0,len(stack)):
            rev_z=len(stack)-z
            if rev_z<len(stack):
                LogWindow.update_log('Z REVERSE GROUPING SLICES '+str(rev_z)+' and '+str(rev_z-1))
                self.grouping_of_stack[rev_z-1]=merge_groups_in_tandem_slices(lower_slice=self.grouping_of_stack[rev_z],upper_slice=self.grouping_of_stack[rev_z-1])
        
        
        
        
        end=time.time()
        LogWindow.update_log('3D GROUPING TIME:'+str(round((end-start),2))+' s')
    
    def calculate_group_volumes(self):
        self.group_information=[]
        surface_area='NA'
        SAV_ratio='NA'
        #find all groups
        set_of_groups=set()
        for z in range(0,len(stack)):
            temp_set=set(self.grouping_of_stack[z].flatten())
            set_of_groups=set_of_groups.union(temp_set)
        if 0 in set_of_groups:
            set_of_groups.remove(0)
        
        #calculate volume for all groups
        for group in set_of_groups:
            list_of_voxel_numbers=[]
            first_appearance=None
            first_appearance_area=0
            number_of_appearances=0
            last_appearance=None
            last_appearance_area=0
            for z in range(0,len(stack)):
                valid_voxels=np.argwhere(self.grouping_of_stack[z]==group)
                amount=int((valid_voxels.size)/2)*Window.scale_factor #divide by two because np argwhere gives two coordinates per datum
                if amount>0:
                    number_of_appearances+=1
                if amount>0 and first_appearance==None:
                    first_appearance=z
                    first_appearance_area=amount
                else:
                    if amount==0 and first_appearance!=None:
                        last_appearance=z-1
                        last_appearance_area=list_of_voxel_numbers[-1]
                        break
                list_of_voxel_numbers.append(amount)
            if last_appearance==None:
                last_appearance=first_appearance
                
            assert first_appearance!=None
            assert first_appearance_area>0
            volume=0
            for amount in list_of_voxel_numbers:
                volume=volume+amount
            
            self.group_information.append([group,volume,first_appearance,first_appearance_area,last_appearance,last_appearance_area,surface_area,SAV_ratio])

        #sort and clean
        self.group_information=sorted(self.group_information,key=lambda x: x[1],reverse=True)

        clean_group=1
        for group in self.group_information:
            for z in range(0,len(stack)):
                array=self.grouping_of_stack[z]
                array=np.where(array==group[0],clean_group,array)
                self.grouping_of_stack[z]=array
            group[0]=clean_group
            clean_group+=1
        
        
        Files.change_and_check_directory(workspace_filename,'differentiated_elements')
        for z in range(0,len(stack)):
            current_slice=self.grouping_of_stack[z]
            image=Image.fromarray(current_slice.astype('uint32'))
            image.save(str(z)+'.tif')
        
        Files.change_or_make_directory(workspace_filename,'python_files')
        with open('group_data.pickle','wb') as output_file:
            pickle.dump(self.grouping_of_stack,output_file)
        
        self.save_group_info_to_pickle()

        self.import_group_info_from_pickle()
        

    @staticmethod
    def find_all_pieces(image_array,group_number):
        if group_number in image_array:
            #group number present
            all_pieces=np.argwhere(image_array==group_number)
            all_pieces=all_pieces.tolist()
            return all_pieces
        else:
            #group number not present
            return None
    
    @staticmethod
    def find_perimeter_pieces(image_array,all_pieces):
        
        perimeter_pieces=[]
        
        for [row,col] in all_pieces:
            try:
                if image_array[row-1,col-1]==0: #NW is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row-1,col+1]==0: #NE is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row+1,col-1]==0: #SW is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row+1,col+1]==0: #SE is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row-1,col]==0: #N is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row,col+1]==0: #E is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row,col-1]==0: #W is blank
                    perimeter_pieces.append([row,col])
                elif image_array[row+1,col]==0: #S is blank
                    perimeter_pieces.append([row,col])
            except IndexError:
                pass
        
        return perimeter_pieces


    def calculate_width(self):
        group_perimeter_pieces=[]
        for row in self.group_information:
            group_number=row[0]
            all_perimeter_pieces=[]
            for z in range(0,len(stack)):
                all_pieces=Grouping.find_all_pieces(self.grouping_of_stack[z],group_number)
                if all_pieces!=None:
                    perimeter_pieces=Grouping.find_perimeter_pieces(self.grouping_of_stack[z],all_pieces)
                    for [row,col] in perimeter_pieces:
                        all_perimeter_pieces.append([row,col,z])
            group_perimeter_pieces.append([group_number,all_perimeter_pieces])
            group_perimeter_pieces=sorted(group_perimeter_pieces,key=lambda x:x[0],reverse=True)
        
        group_width_coords=[]
        for row in group_perimeter_pieces:
            group_number=row[0]
            all_modulus_lengths=[]
            start=time.time()
            for first_coord in row[1]:
                sub_modulus_lengths=[]
                for second_coord in row[1]:
                    if first_coord!=second_coord:
                        x_diff=abs(first_coord[0]-second_coord[0])
                        y_diff=abs(first_coord[1]-second_coord[1])
                        z_diff=abs(first_coord[2]-second_coord[2])
                        modulus=math.sqrt(x_diff**2+y_diff**2+z_diff**2)
                        sub_modulus_lengths.append([modulus,first_coord,second_coord])
                if len(sub_modulus_lengths)>0: #will equal zero if there is a lone pixel
                    max_modulus=max(sub_modulus_lengths) #finds max according to item at index 0
                    all_modulus_lengths.append(max_modulus) #prevent build up of memory
                    
                    sub_modulus_lengths=[]
            end=time.time()
            print('time: ',str(round((end-start),2)),'s')
            
            
            all_modulus_lengths=sorted(all_modulus_lengths, key=lambda x:x[0],reverse=True)
            if len(all_modulus_lengths)>0:
                max_modulus=all_modulus_lengths[0]
                ######scaling#####
                first_coord=max_modulus[1]
                
                first_coord=np.array(first_coord)*Window.scale_factor
                
                second_coord=max_modulus[2]
                second_coord=np.array(second_coord)*Window.scale_factor
                x_diff=abs(first_coord[0]-second_coord[0])
                y_diff=abs(first_coord[1]-second_coord[1])
                z_diff=abs(first_coord[2]-second_coord[2])
                scaled_modulus=math.sqrt(x_diff**2+y_diff**2+z_diff**2)
                max_modulus[0]=scaled_modulus
                ##################
                group_width_coords.append([max_modulus,group_number])

        self.width_coordinates=group_width_coords
        self.save_group_data_to_csv()

    def show_width_coords(self):
        for group in self.width_coordinates:
            col=group[0][1][1]
            row=group[0][1][0]
            GroupedView.group_preview.create_rectangle(col,row,col,row,fill='cyan',outline='green')
            col1=group[0][2][1]
            row1=group[0][2][0]
            GroupedView.group_preview.create_rectangle(col1,row1,col1,row1,fill='magenta',outline='red')
            GroupedView.group_preview.create_line(col,row,col1,row1,fill='yellow')
            
    def create_width_stack(self):
        width_stack=copy.deepcopy(self.colored_stack)
        def draw_point(col,row,z,rowspan,colspan,zspan,color=(255,255,255)):
            try:
                for z in range(z-int(zspan/2),z+int(zspan/2)):
                    if z>=0: #avoid indexing backwards -1, -2 etc...
                        for row_span in range(1,rowspan+1):
                            for col_span in range(1,colspan+1):
                                width_stack[z][row,col]=color
                                width_stack[z][row-row_span,col]=color
                                width_stack[z][row,col-col_span]=color
                                width_stack[z][row-row_span,col-col_span]=color
                                width_stack[z][row+row_span,col]=color
                                width_stack[z][row,col+col_span]=color
                                width_stack[z][row+row_span,col+col_span]=color
                                width_stack[z][row-row_span,col+col_span]=color
                                width_stack[z][row+row_span,col-col_span]=color
            except IndexError:
                pass

        for group in self.width_coordinates:
            col=group[0][1][1]
            row=group[0][1][0]
            z=group[0][1][2]
            draw_point(col,row,z,2,2,3)
            
            col1=group[0][2][1]
            row1=group[0][2][0]
            z1=group[0][2][2]
            draw_point(col1,row1,z1,2,2,3)

            dcol=abs(col-col1)
            drow=abs(row-row1)
            dz=abs(z-z1)
            if dz>0:
                increment_col=int(dcol/dz)
                increment_row=int(drow/dz)

                if z1>z:
                    for new_z in range(z,z1):
                        if col1>col:
                            new_col=col+increment_col
                        else:
                            new_col=col-increment_col
                        if row1>row:
                            new_row=row+increment_row
                        else:
                            new_row=row-increment_row

                        draw_point(new_col,new_row,new_z,2,2,3)
                        col=new_col
                        row=new_row
            elif dz==0:
                steps_from_col=int(dcol/6)
                steps_from_row=int(drow/6)
                steps=min([steps_from_row,steps_from_col])
                for increment in range(0,steps):
                    if col1>col:
                        new_col=col+steps_from_col
                        if new_col>=col1:
                            continue
                    elif col1<col:
                        new_col=col-steps_from_col
                        if new_col<=col1:
                            continue
                    elif col1==col:
                        new_col=col
                    if row1>row:
                        new_row=row+steps_from_row
                        if new_row>=row1:
                            continue
                    elif row1<row:
                        new_row=row-steps_from_row
                        if new_row<=row1:
                            continue
                    elif row1==row:
                        new_row=row
                    draw_point(new_col,new_row,z,2,2,3,color=(255,255,255))
                    
                    col=new_col
                    row=new_row
            
        
        new_folder=workspace_filename+'_show_width'
        os.chdir(directory_name) #return to parent directory before creating new folder
        try:
            shutil.rmtree(new_folder) #delete the folder if it already exists
        except:
            pass #if there is no folder to replace
        os.mkdir(new_folder) #create folder
        os.chdir(new_folder) #move into folder

        for z in range(0,len(stack)):
            current_slice=width_stack[z]
            image=Image.fromarray(current_slice)
            image.save(str(z)+'.tif')

    def filter_groups(self):
        if SegmentedView.segmented_vol_filter_size_entry==None:
            return
        filter_size=SegmentedView.segmented_vol_filter_size_entry.get()
        if filter_size=='':
            return
        filter_size=int(filter_size)
        filtered_groups=[]
        deleted_groups=[]
        for row in self.group_information:
            if row[1]>=filter_size:
                filtered_groups.append(row)
            else:
                deleted_groups.append(row)
        
        self.save_group_data_to_csv(file_suffix='_unfiltered')
        self.group_information=filtered_groups
        self.save_group_data_to_csv()

        Files.change_or_make_directory(workspace_filename,'python_files')
        with open('group_data.pickle','wb') as output_file:
            pickle.dump(self.grouping_of_stack,output_file)

        for row in deleted_groups:
            first_appearance=row[2]
            last_appearance=row[4]
            for z in range(first_appearance,last_appearance+1):
                self.grouping_of_stack[z]=np.where(self.grouping_of_stack[z]==row[0],0,self.grouping_of_stack[z])
                rgb_list=[]
                for value in np.nditer(self.grouping_of_stack[z]):
                    if value:
                        rgb_list.append((255,0,255,100))
                    else:
                        rgb_list.append((0,0,0,0))
                rgb_array=np.array(rgb_list,dtype=np.uint8).reshape(source_image_width,source_image_height,4)
                segmented_vol_segmented_view.segmented_stack[z].image_array=rgb_array
                SegmentedView.segmented_vol_segmented_stack[z].image_array=rgb_array
                length=last_appearance-first_appearance
                if length==0:
                    length=1
                log_window_progress_bar.create_z_progress((z-first_appearance-1),length)
        
        LogWindow.update_log('Filtered groups. Minimum volume '+str(filter_size))
        os.chdir(directory_name)

        folder_name='differentiated_elements_'+str(filter_size)+'_filtered'
        if os.path.isdir(folder_name):
            shutil.rmtree(folder_name)
        os.mkdir(folder_name)
        os.chdir(folder_name)
        for z in range(0,len(stack)):
            current_slice=self.grouping_of_stack[z]
            image=Image.fromarray(current_slice.astype('uint32'))
            image.save(str(z)+'.tif')
            log_window_progress_bar.create_z_progress(z,len(stack))
        log_window_progress_bar.hide_z_progress()
        LogWindow.update_log('Saved differentiated elements')
        
        self.color_groups(color_scheme_monet)
        LogWindow.update_log('Colored differentiated elements')
        
        SegmentedView.save_segmented_vol_segmented_stack(file_suffix='_filtered')
        LogWindow.update_log('Saved segmented layer')

        segmented_vol_segmented_view.display_image(current_z)
        
    def filter_groups_by_gaussian(self,sigma,color_scheme):
        start=time.time()
        
        for z in range(0,len(stack)):
            current_array=self.grouping_of_stack[z]
            if z ==0:
                individual_groups= set(current_array.flatten())
            if z > 0:
                temp_set=set(current_array.flatten())
                individual_groups=individual_groups.union(temp_set)
            if 0 in individual_groups:
                individual_groups.remove(0)
        individual_groups=list(individual_groups)
        

        color_index=np.arange(start=0,stop=len(color_scheme)-1,step=1)
        repeats=math.ceil(len(individual_groups)/len(color_scheme))
        if repeats>=1:
            count=0
            while count < repeats:
                color_index=np.concatenate([color_index,color_index])
                count+=1
        color_index=list(color_index)
        Grouping.color_index=color_index

        count=0
        group_dictionary={}
        while count < len(individual_groups):
            group_dictionary[individual_groups[count]]=color_scheme[color_index[count]]
            count+=1

        
        rgba_smooth_stack=[]
        for z in range(0,len(stack)):
            current_array=self.grouping_of_stack[z]
            rgba_list_r=[]
            rgba_list_g=[]
            rgba_list_b=[]
            for value in np.nditer(current_array):
                if value:
                    rgba=group_dictionary[int(value)]
                    rgba_list_r.append(rgba[0])
                    rgba_list_g.append(rgba[1])
                    rgba_list_b.append(rgba[2])
                else:
                    rgba_list_r.append((0))
                    rgba_list_g.append((0))
                    rgba_list_b.append((0))
            rgba_array_r=np.array(rgba_list_r,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_r_gauss=gaussian_filter(rgba_array_r,sigma)
            rgba_array_g=np.array(rgba_list_g,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_g_gauss=gaussian_filter(rgba_array_g,sigma)
            rgba_array_b=np.array(rgba_list_b,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_b_gauss=gaussian_filter(rgba_array_b,sigma)
            
            rgba_array_total_gauss=np.dstack((rgba_array_r_gauss,rgba_array_g_gauss,rgba_array_b_gauss))
            rgba_array_total_gauss=np.array(rgba_array_total_gauss,dtype=np.uint8).reshape(source_image_width,source_image_height,3)

            rgba_smooth_stack.append(rgba_array_total_gauss)

        self.colored_stack=rgba_smooth_stack
        if sigma>0:
            new_folder='differentiated_elements_Gaussian_filter' #designated directory
        elif sigma==0: #just coloring and not applying the filter
            new_folder='differentiated_elements_colored'

        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory(new_folder,parent_directory=False)    

        for z in range(0,len(stack)):
            current_slice=rgba_smooth_stack[z]
            image=Image.fromarray(current_slice)
            image.save(str(z)+'.tif')
        
        end=time.time()
        LogWindow.update_log('Colored/filtered segmented volume: '+str(round((end-start),2))+' s')    


    def filter_groups_by_gaussian_final_touches(self,sigma,color_scheme):
        start=time.time()
        
        for z in range(0,len(stack)):
            current_array=self.grouping_of_stack[z]
            if z ==0:
                individual_groups= set(current_array.flatten())
            if z > 0:
                temp_set=set(current_array.flatten())
                individual_groups=individual_groups.union(temp_set)
            if 0 in individual_groups:
                individual_groups.remove(0)
        individual_groups=list(individual_groups)
        

        color_index=np.arange(start=0,stop=len(color_scheme)-1,step=1)
        repeats=math.ceil(len(individual_groups)/len(color_scheme))
        if repeats>=1:
            count=0
            while count < repeats:
                color_index=np.concatenate([color_index,color_index])
                count+=1
        color_index=list(color_index)
        Grouping.color_index=color_index

        count=0
        group_dictionary={}
        while count < len(individual_groups):
            group_dictionary[individual_groups[count]]=color_scheme[color_index[count]]
            count+=1

        
        rgba_smooth_stack=[]
        for z in range(0,len(stack)):
            current_array=self.final_touches_stack[z]
            
            rgba_list_r=current_array.flatten()
            rgba_list_r=rgba_list_r[0::3]
            rgba_list_g=current_array.flatten()
            rgba_list_g=rgba_list_g[1::3]
            rgba_list_b=current_array.flatten()
            rgba_list_b=rgba_list_b[2::3]
        
            rgba_array_r=np.array(rgba_list_r,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_r_gauss=gaussian_filter(rgba_array_r,sigma)
            rgba_array_g=np.array(rgba_list_g,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_g_gauss=gaussian_filter(rgba_array_g,sigma)
            rgba_array_b=np.array(rgba_list_b,dtype=np.uint8).reshape(source_image_width,source_image_height)
            rgba_array_b_gauss=gaussian_filter(rgba_array_b,sigma)
            
            rgba_array_total_gauss=np.dstack((rgba_array_r_gauss,rgba_array_g_gauss,rgba_array_b_gauss))
            rgba_array_total_gauss=np.array(rgba_array_total_gauss,dtype=np.uint8).reshape(source_image_width,source_image_height,3)

            rgba_smooth_stack.append(rgba_array_total_gauss)

        self.final_touches_stack=rgba_smooth_stack
        
      


    def color_groups(self,color_scheme):
        self.filter_groups_by_gaussian(sigma=0,color_scheme=color_scheme)

    def smoothen_elements(self,color_scheme):

        def get_shifted_array(input_array,direction):
            
            def shift_array(input_array,direction):
                if direction=='S': #shift array south/downward
                    output_array=np.insert(input_array,obj=0,values=0,axis=0) #insert row of zeros at the top to shift array down
                    output_array=np.delete(output_array,obj=-1,axis=0) #delete last row to maintain dimensions
                elif direction=='N': #shift array north/upward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=0) #insert row of zeros at the bottom to shift array up
                    output_array=np.delete(output_array,obj=0,axis=0) #delete first row to maintain dimensions
                elif direction=='E': #shift array west/leftward
                    output_array=np.insert(input_array,obj=0,values=0,axis=1) #insert col of zeros on the left to shift array right
                    output_array=np.delete(output_array,obj=-1,axis=1) #delete right-most col to maintain dimensions
                elif direction=='W': #shift array west/leftward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=1) #insert col of zeros on the right to shift array left
                    output_array=np.delete(output_array,obj=0,axis=1) #delete left-most col to maintain dimensions
                return output_array
            
            if direction=='NW':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'W')
            elif direction=='NE':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'E')
            elif direction=='SW':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'W')
            elif direction=='SE':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'E')
            else:
                output_array=shift_array(input_array,direction)
            return output_array
    
        directions=['N','NE','E','SE','S','SW','W','NW'] #8 directions so 8 images

        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory('smoothened_colored_stack',parent_directory=False)
        
        
        for z in range(0,len(stack)):
            
            image=self.grouping_of_stack[z]
            binary_image=np.where(image!=0,1,0)
            working_image=binary_image
            count=0
            while count<5: #reiterate 5 times to make edges more smooth
                sum_image=np.zeros((source_image_width,source_image_height),dtype=int)
                for direction in directions:
                    shifted_array=get_shifted_array(working_image,direction=direction)
                    sum_image=sum_image+shifted_array
                median_image=np.where(sum_image>=5,1,0) #8 is the max and 0 is the minimum. 5 or more leads to median score of 0.5-1
                working_image=median_image
                count+=1
            grouped_image=self.grouping_of_stack[z]
            smooth_grouped_image=np.where(median_image==0,0,grouped_image)
            smooth_grouped_image=np.array(smooth_grouped_image,dtype=np.uint8)

            self.smoothened_grouped_stack.append(smooth_grouped_image)
        
        for z in range(0,len(stack)):
            current_array=self.grouping_of_stack[z]
            if z ==0:
                individual_groups= set(current_array.flatten())
            if z > 0:
                temp_set=set(current_array.flatten())
                individual_groups=individual_groups.union(temp_set)
            if 0 in individual_groups:
                individual_groups.remove(0)
        individual_groups=list(individual_groups)

        color_index=np.arange(start=0,stop=len(color_scheme)-1,step=1)
        repeats=math.ceil(len(individual_groups)/len(color_scheme))
        if repeats>=1:
            count=0
            while count < repeats:
                color_index=np.concatenate([color_index,color_index])
                count+=1
        color_index=list(color_index)

        count=0
        group_dictionary={}
        while count < len(individual_groups):
            group_dictionary[individual_groups[count]]=color_scheme[color_index[count]]
            count+=1

        rgba_smooth_stack=[]
        for z in range(0,len(stack)):
            
            current_array=self.smoothened_grouped_stack[z]
            rgb_list=[]
            for value in np.nditer(current_array):
                if value:
                    rgb=group_dictionary[int(value)]
                    rgb_list.append((rgb[0],rgb[1],rgb[2]))
                else:
                    rgb_list.append((0,0,0))
            rgb_array=np.array(rgb_list,dtype=np.uint8).reshape(source_image_width,source_image_height,3)
            rgba_smooth_stack.append(rgb_array)

            image=Image.fromarray(rgb_array)
            string_z_pos=StringZ.int_to_3_dec_string(z)
            image.save(string_z_pos+'.tif')
        
    def smoothen_final_touches(self,color_scheme,factor):

        def get_shifted_array(input_array,direction):
            
            def shift_array(input_array,direction):
                if direction=='S': #shift array south/downward
                    output_array=np.insert(input_array,obj=0,values=0,axis=0) #insert row of zeros at the top to shift array down
                    output_array=np.delete(output_array,obj=-1,axis=0) #delete last row to maintain dimensions
                elif direction=='N': #shift array north/upward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=0) #insert row of zeros at the bottom to shift array up
                    output_array=np.delete(output_array,obj=0,axis=0) #delete first row to maintain dimensions
                elif direction=='E': #shift array west/leftward
                    output_array=np.insert(input_array,obj=0,values=0,axis=1) #insert col of zeros on the left to shift array right
                    output_array=np.delete(output_array,obj=-1,axis=1) #delete right-most col to maintain dimensions
                elif direction=='W': #shift array west/leftward
                    output_array=np.insert(input_array,obj=-1,values=0,axis=1) #insert col of zeros on the right to shift array left
                    output_array=np.delete(output_array,obj=0,axis=1) #delete left-most col to maintain dimensions
                return output_array
            
            if direction=='NW':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'W')
            elif direction=='NE':
                output_array=shift_array(input_array,'N')
                output_array=shift_array(output_array,'E')
            elif direction=='SW':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'W')
            elif direction=='SE':
                output_array=shift_array(input_array,'S')
                output_array=shift_array(output_array,'E')
            else:
                output_array=shift_array(input_array,direction)
            return output_array
    
        directions=['N','NE','E','SE','S','SW','W','NW'] #8 directions so 8 images

        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory('smoothened_colored_stack',parent_directory=False)
        
        
        for z in range(0,len(stack)):

            image=self.grouping_of_stack[z]
            binary_image=np.where(image!=0,1,0)
            working_image=binary_image
            count=0
            while count<factor: #reiterate N times to make edges more smooth
                sum_image=np.zeros((source_image_width,source_image_height),dtype=int)
                for direction in directions:
                    shifted_array=get_shifted_array(working_image,direction=direction)
                    sum_image=sum_image+shifted_array
                median_image=np.where(sum_image>=5,1,0) #8 is the max and 0 is the minimum. 5 or more leads to median score of 0.5-1
                working_image=median_image
                count+=1
            grouped_image=self.grouping_of_stack[z]
            smooth_grouped_image=np.where(median_image==0,0,grouped_image)
            smooth_grouped_image=np.array(smooth_grouped_image,dtype=np.uint8)

            self.final_touches_stack[z]=smooth_grouped_image
        
        for z in range(0,len(stack)):
            current_array=self.grouping_of_stack[z]
            if z ==0:
                individual_groups= set(current_array.flatten())
            if z > 0:
                temp_set=set(current_array.flatten())
                individual_groups=individual_groups.union(temp_set)
            if 0 in individual_groups:
                individual_groups.remove(0)
        individual_groups=list(individual_groups)

        color_index=np.arange(start=0,stop=len(color_scheme)-1,step=1)
        repeats=math.ceil(len(individual_groups)/len(color_scheme))
        if repeats>=1:
            count=0
            while count < repeats:
                color_index=np.concatenate([color_index,color_index])
                count+=1
        color_index=list(color_index)

        count=0
        group_dictionary={}
        while count < len(individual_groups):
            group_dictionary[individual_groups[count]]=color_scheme[color_index[count]]
            count+=1

        for z in range(0,len(stack)):
            
            current_array=self.final_touches_stack[z]
            rgb_list=[]
            for value in np.nditer(current_array):
                if value:
                    rgb=group_dictionary[int(value)]
                    rgb_list.append((rgb[0],rgb[1],rgb[2]))
                else:
                    rgb_list.append((0,0,0))
            rgb_array=np.array(rgb_list,dtype=np.uint8).reshape(source_image_width,source_image_height,3)
            self.final_touches_stack[z]=rgb_array
            
        
    def open_grouped_stack(self,volume_feature):
        global grouped_stack
        os.chdir(directory_name)
        folder_name=workspace_filename+'_'+str(volume_feature)+'_group'
        os.chdir(folder_name)

        try:
            bool_stack=self.convert_RGBA_to_bool()
            grouped_stack=copy.deepcopy(bool_stack)
            for z in range(0,len(bool_stack)):
                grouped_stack[z].image_array=np.where(grouped_stack[z].image_array==True,0,0) #make an empty stack
                log_window_progress_bar.create_z_progress(z,len(bool_stack))

            for z in range (0,len(grouped_stack)):
                current_image=Image.open('filtered_grouping_of_'+str(z)+'.tif')
                current_array=np.array(current_image,dtype='uint8')
                grouped_stack[z].image_array=current_array
                log_window_progress_bar.create_z_progress(z,len(grouped_stack))

            z=1
            log_window_progress_bar.create_z_progress(z,4)
            with open('list_of_groups.pickle','rb') as input_file:
                global list_of_groups
                list_of_groups=pickle.load(input_file)
                LogWindow.update_log('Imported list of groups')
                z=2
                log_window_progress_bar.create_z_progress(z,4)

            with open('group_volumes.pickle','rb') as input_file:
                global group_volumes
                group_volumes=pickle.load(input_file)
                LogWindow.update_log('Imported group volumes')
                z=3
                log_window_progress_bar.create_z_progress(z,4)
            z=4
            log_window_progress_bar.create_z_progress(z,4)
            log_window_progress_bar.hide_z_progress()
            
            LogWindow.update_log('Imported segmented groups')
        except:
            LogWindow.update_log('Failed to import segmented groups')

    def convert_RGBA_to_bool(self):
        z=0
        bool_stack=[]
        while z < len(self.segmented_stack):
            current_image=self.segmented_stack[z].image_array
            limited_array=np.delete(current_image,[0,1,2],axis=2)
            limited_array=np.where(limited_array>0,True,False)

            bool_array=np.array(limited_array).reshape(source_image_height,source_image_width)
            bool_array=PixelArray(bool_array)
            bool_stack.append(bool_array)
            z=z+1
        return bool_stack

    def save_group_info_to_pickle(self):
        Files.change_and_check_directory(workspace_filename,'python_files')

        try: #will not work before file is selected
            with open('group_information.pickle','wb') as output_file:
                pickle.dump(self.group_information,output_file)
        except:
            pass
        os.chdir(directory_name)

    def import_group_info_from_pickle(self):
        
        Files.change_and_check_directory(workspace_filename,'python_files')
        if os.path.isfile('group_information.pickle'):
            with open('group_information.pickle','rb') as input_file:
                self.group_information=pickle.load(input_file)
                LogWindow.update_log('Loaded quantitative information')
        
        if os.path.isfile('group_data.pickle'):
            with open('group_data.pickle','rb') as input_file:
                self.grouping_of_stack=pickle.load(input_file)
                LogWindow.update_log('Loaded grouped voxels')
        
            self.color_groups(color_scheme=color_scheme_monet)

    def save_group_data_to_csv(self,file_suffix=''):
 
        foldername='quantitation'+file_suffix
        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory(foldername,parent_directory=False)
       
        csv_filename=workspace_filename+'_quantitation'+file_suffix+'.csv'
        if len(self.width_coordinates)==0:
            with open(csv_filename, mode='w') as csv_file:
                fieldnames = ['group_number','volume']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for group in self.group_information:
                    writer.writerow({'group_number': group[0],'volume':group[1]})
        else:
            with open(csv_filename, mode='w') as csv_file:
                fieldnames = ['group_number','volume','width']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for index in range(0,len(self.group_information)):
                    try:
                        group=self.group_information[index]
                        matching_group=self.width_coordinates[(-index-1)]
                        print(group[0],matching_group[1])
                        #assert group[0]==matching_group[1]
                        width=matching_group[0][0]
                        writer.writerow({'group_number': group[0],'volume':group[1],'width':width})
                    except IndexError:
                        pass
        LogWindow.update_log('Saved quantitative data to file: '+str(workspace_filename)+'_quantitation/')
        
#DIRECTORY##########################################################################################################################


directory_name = os.getcwd() #get the directory name without the script filename at the end
Files.change_or_make_directory('contour_files')
directory_name = os.getcwd()
print(directory_name)

    
    
#GLOBAL VARIABLES###################################################################################################################
centroid_super_list=[]
centroid_adjusted_list=[]
color=None
color_scheme_choice='Monet (default)'
color_segmented_vol='magenta'
connector_lines=[]
conversion_ratio=1 #the ratio of z depth to source_image_stack width, used to scale the scroll bar
current_z=1 #used by Window class to denote z slice in loaded image
current_z_left=1 #remembers z of left preview in case current_z changed by right preview
first_node_exists=False
first_node=None
grouped_stack=[]
group_volumes=[]
group_window=None
grouped_view=None
groups=None
histogram=None
imported_segmented_volume=False
interval_entry=None
iterator=0
left_scroll_bar=None
limit_entry=None
list_of_groups=[]
load_image=None
log_box=None
lower_threshold_entry_segmented_vol=0
mag_image_array=None
message_template=''
minimum_width_entry_segmented_vol=None
mito_pixel_list=[]
segmented_vol_segmented_window=None
modified=False
new_workspace=None
volume_feature=None
point_display=None
point_size_entry=None
point_size=6
preview_stack=[]
rangegram=None
rangegram_data=(None,None)
reduced_group_table=[]
right_scroll_bar=None
scale_entry=None
scroll_line=None
scroll_position=None
scale_factor=0
second_node_exists=False
second_node=None
segmented_canvas=None
selection_window=None
shuffle_colors=False
stack=[] #list containing each image array as an object of the PixelArray class
temp_stack_storage=[]
threading_choice=False #start program in off position
threshold_array=[]
source_image_canvas=None
source_image_height=0
source_image_width=0
upper_threshold_entry_segmented_vol=255
workspace_filename='autosave'
workspace_index=[]
z_depth_entry=None
z_start_entry=None
z_end_entry=None

email_string='''\nFor queries and reporting bugs, email contourqueries@gmail.com'''


color_scheme_basic=[(78,181,216),(253,209,76),(200,52,8),(98,192,120),(140,99,159),(214,75,122),(132,246,210),(11,83,130),(251,254,245),(254,217,24),(95,144,120),(160,119,129),(215,92,4),(210,160,165),(122,203,176),(154,151,33)]
color_scheme_rembrandt=[(100,114,113),(252,241,210),(254,205,90),(200,97,54),(183,130,86),(183,130,86),(244,232,197),(183,117,111),(139,102,73),(254,219,120),(163,157,123),(254,233,198),(212,82,41),(208,146,85),(255,221,116),(255,244,212),(175,175,162),(222,173,115)]
color_scheme_monet=[(127,148,133),(160,138,125),(131,167,178),(161,94,94),(187,185,186),(148,158,123),(174,164,169),(87,108,142),(170,163,157),(192,145,153),(134,163,135),(154,139,135),(129,169,190),(151,87,84),(136,156,134),(198,203,196),(197,167,169),(129,161,176)]
color_scheme_pinks=[(230,25,230),(212,34,55),(158,77,240),(191,64,6),(227,163,193),(230,129,230),(232,88,105),(192,157,227),(184,90,72),(235,87,156),(217,204,230),(173,111,118),(163,34,163),(219,11,108),(126,21,232),(252,197,203),(173,120,173),(166,31,94),(110,41,179)]
color_scheme_blues=[(0, 162, 255),(2, 242, 146),(7, 218, 250),(158, 232, 230),(0, 255, 251),(94, 191, 247),(21, 158, 103),(96, 227, 247),(77, 171, 168),(211, 245, 244),(141, 205, 242),(105, 199, 161),(165, 232, 242),(18, 181, 176),(63, 207, 212),(105, 160, 191),(181, 232, 211),(118, 175, 184),(57, 138, 184),(15, 242, 219),(76, 161, 176),(0, 107, 168),(22, 165, 184)]
color_scheme_yellows=[(255, 251, 8),(252, 219, 3),(229, 237, 140),(214, 188, 19),(255, 254, 181),(217, 214, 22),(234, 255, 0),(240, 224, 122),(199, 198, 90),(196, 209, 46),(227, 225, 68),(229, 242, 82),(212, 193, 72),(250, 248, 145)]
color_scheme_kandinsky=[(160,56,79),(143,144,92),(227,103,51),(188,125,142),(220,165,39),(189,211,235),(151,148,96),(47,81,178),(153,93,99),(225,128,51),(211,206,210),(73,127,114),(187,140,135),(230,215,189),(32,123,190),(218,171,104),(177,45,67),(228,237,238),(116,138,74),(238,166,56),(177,191,215),(215,207,221),(176,123,143),(32,123,190),(215,207,221),(163,179,194),(116,138,74),(68,110,186)]
color_scheme_dictionary={'basic':color_scheme_basic,'blues':color_scheme_blues,'Kandinsky':color_scheme_kandinsky,'Monet (default)':color_scheme_monet,'pinks':color_scheme_pinks,'Rembrandt':color_scheme_rembrandt,'yellows':color_scheme_yellows}
color_scheme=color_scheme_monet
color_scheme= color_scheme * 50
rotation_color_scheme_blue=['blue','blue','blue']
rotation_color_scheme_red=['red','red','red']
rotation_color_scheme_yellow=['yellow','yellow','yellow']
rotation_color_scheme=rotation_color_scheme_blue + rotation_color_scheme_yellow + (rotation_color_scheme_red*500)

point_size_list=[np.array((1)),\
np.array(([1,1,1],[1,1,1],[1,1,1])),\
np.array(([0,1,1,1,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0])),\
np.array(([0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[0,1,1,1,1,1,0],[0,0,1,1,1,0,0])),\
np.array(([0,0,0,1,1,1,0,0,0],[0,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,0,0,0])),\
np.array(([0,0,0,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,0,0,0])),\
np.array(([0,0,0,0,1,1,1,1,1,0,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,1,1,0,0],[0,0,0,0,1,1,1,1,1,0,0,0,0])),\
np.array(([0,0,0,0,0,1,1,1,1,1,0,0,0,0,0],[0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,0,1,1,1,1,1,0,0,0,0,0])),\
np.array(([0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0],[0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0],[0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0]))]



#FUNCTIONS##########################################################################################################################
def reload_window():
    global segmented_vol_segmented_window
    global segmented_vol_segmented_view
    
    SegmentedView.save_segmented_vol_segmented_stack()
    segmented_vol_segmented_window.withdraw()
    SegmentedView.segmented_vol_segmented_stack=[]
    del segmented_vol_segmented_window #remove from the namespace / make unreferenced
    try:
        del segmented_vol_segmented_view
    except NameError:
        pass
    gc.collect(generation=2) #garbage collection of unreferenced data in generation 2
    try:
        gc.collect(generation=1)
        gc.collect(generation=0)
    except:
        pass
    segmented_vol_segmented_window=Toplevel() #Toplevel is used when functions occur between different Tk windows
    segmented_vol_segmented_window.title('Segmented Volume')
    segmented_vol_segmented_window.withdraw()
    volume_feature='Segmented_Vol'
    the_segment=SegmentedArray(image_array=None,master=segmented_vol_segmented_window,volume_feature=volume_feature)
    segmented_vol_segmented_window.deiconify()
    open_segmented_vol_segmentation()


def rgb2hex(r,g,b):
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

def enable_filter_groups():

    groups.filter_groups()

def enable_apply_final_touches():
    groups.final_touches_stack=groups.colored_stack #copy colored stack to work with
    if SegmentedView.smoothen_toggle==True:
        try:
            factor=SegmentedView.smoothen_factor_entry.get()
            factor=int(factor)
        except:
            LogWindow.update_log('Could not apply smoothening. Check factor')
            return
        groups.smoothen_final_touches(color_scheme=color_scheme,factor=factor)
    if SegmentedView.Gaussian_toggle==True:
        try:
            sigma=SegmentedView.sigma_entry.get()
            sigma=float(sigma)
        except:
            LogWindow.update_log('Could not apply Gaussian filter. Check sigma')
            return
        groups.filter_groups_by_gaussian_final_touches(sigma=sigma,color_scheme=color_scheme)
    

    Files.change_and_check_directory(workspace_filename)
    Files.change_and_overwrite_directory('differentiated_elements_final_touches',parent_directory=False)    
    
    
    for z in range(0,len(stack)):
        current_slice=groups.final_touches_stack[z]
        image=Image.fromarray(current_slice)
        image.save(str(z)+'.tif')

    LogWindow.update_log('Applied final touches')


def group_voxels(import_option=False):
    global groups
    global grouped_view
    if import_option==False:
        if len(SegmentedView.segmented_vol_segmented_stack)>0:
            groups=Grouping(SegmentedView.segmented_vol_segmented_stack)
            groups.group_by_arrays()
            groups.color_groups(color_scheme=color_scheme_monet)
            groups.calculate_group_volumes()
            groups.save_group_data_to_csv()
            
    
    if import_option==True:
        groups=Grouping('importing')
        groups.import_group_info_from_pickle()
        groups.color_groups(color_scheme=color_scheme_monet)
        

    grouped_view=GroupedView(master=group_window,foldername='quantitation',grouping_data=groups)
    grouped_view.display_grouped_stack()
    grouped_view.display_scroll_bar(initial=True)
    grouped_view.display_stack_extremes()
    grouped_view.display_data_table(color_scheme=color_scheme_monet)
    grouped_view.display_buttons()


    
def enable_calculate_widths():    
    warning_message='''The Calculate Width function will only produce reliable measurements if your original voxel dimensions are cubic (x=y=z).
This function should be avoided if the original voxel dimensions are cuboidal.

Proceed?'''
    continue_option=messagebox.askyesno(title='Warning: cubic voxel dimensions required',message=warning_message)
    if continue_option==False:
        return
    warning_message='''The Calculate Width function can be time-consuming. 

It can take several minutes or hours depending on the size of your data and the size of the segmented elements.

Proceed?'''
    continue_option=messagebox.askyesno(title='Warning: time-consuming function',message=warning_message)
    if continue_option==False:
        return

    groups.calculate_width()
    groups.show_width_coords()
    groups.create_width_stack()


def bind_collect_pixels():
    try:
        source_image_canvas.bind('<B1-Motion>',collect_pixels)
    except AttributeError:
        pass

def shrink_list(the_list,lower,upper):
    try:
        if min(the_list)<int(lower):
            index=0
            count=0
            the_list=sorted(the_list)
            while index<len(the_list):
                if the_list[index]<=int(lower):
                    del the_list[index]
                else:
                    index=index+1
        
        elif min(the_list)>int(lower):
            pass
              
        
        if max(the_list)>int(upper):
            index=0
            count=0
            the_list=sorted(the_list,reverse=True)
            while index<len(the_list):
                if the_list[index]>int(upper):
                    count=count+1
                index=index+1
            del the_list[0:count]
        return the_list
    except ValueError:
        return the_list #returns the original untouched list

  
def collect_pixels(event):
    if volume_feature==None:
        return
    
    global mito_pixel_list
    global rangegram_data

    def update_rangegram(index):
        global rangegram_data
        rangegram_data=Rangegram(mito_pixel_list)
        rangegram_data.display_rectangle(rangegram)
        



    pixel_value=get_pixel_value(stack,current_z_left+1,event.y-4,event.x-3) #row_index=y & column_index=x
    source_image_canvas.create_oval(event.x-2,event.y-2,event.x+2,event.y+2,fill=color,outline='')

    if volume_feature=='Segmented_Vol':
        mito_pixel_list=shrink_list(mito_pixel_list,lower=lower_threshold_entry_segmented_vol.get(),upper=upper_threshold_entry_segmented_vol.get())
        mito_pixel_list.append(pixel_value)
        histo=Histogram(volume_feature=volume_feature,color=color_segmented_vol,order='1',pixel_list=mito_pixel_list,master=import_window)
        histo.display_histogram()
        update_rangegram(0)

    histo=Histogram(volume_feature=volume_feature,color=color_segmented_vol,order='1',pixel_list=mito_pixel_list,master=import_window)
    histo.update_histogram()


    if volume_feature=='Segmented_Vol':
        #global mito_pixel_list
        mito_pixel_list.append(pixel_value)

        histo.update_histogram()
        if len(mito_pixel_list)>=2:
            segmented_vol.display_buttons(lower=min(mito_pixel_list),upper=max(mito_pixel_list))


def get_pixel_value(image_stack,z_slice,row_index,column_index):
    if z_slice!=None:
        try:
            working_slice=image_stack[int(z_slice)].image_array #image array stored in an object of a class
            return working_slice[row_index,column_index]
        except:
            pass
        try:
            working_slice=image_stack[int(z_slice)] #image array stored in a list
            return working_slice[row_index,column_index]
        except:
            pass
    else:
        return image_stack[row_index,column_index]

def apply_threshold_to_pixel(pixel_value,lower_threshold,upper_threshold):
    if pixel_value==-1: #this will be case if excluded from selection
        return False
    if int(pixel_value)>int(upper_threshold):
        return False
    elif int(pixel_value)<int(lower_threshold):
        return False
    else:
        return True


    if len(sample)>=3:
        mean_x=calculate_mean(sample)
        deviation_exponent_2=0
        for x in sample:
            x_dev=(x-mean_x)**2
            deviation_exponent_2=deviation_exponent_2+x_dev
        deviation_exponent_4=0
        for x in sample:
            x_dev=(x-mean_x)**4
            deviation_exponent_4=deviation_exponent_4+x_dev
        second_moment=deviation_exponent_2/len(sample)
        fourth_moment=deviation_exponent_4/len(sample)
        kurtosis=fourth_moment/(second_moment**2)
        return kurtosis
    else:
        return None


def save_workspace(overwrite_query=False):
    global workspace_index
    global file_path
    
   
    if os.path.isdir(workspace_filename):
        if overwrite_query:
            if workspace_filename!='workspace_autosave':
                warning_message='A workspace named '+str(workspace_filename)+' already exists.\
    Are you sure you want to replace it?'
                confirm_overwrite_window=messagebox.askokcancel('Workspace Exists',warning_message)
                if confirm_overwrite_window==False:
                    pass
                elif confirm_overwrite_window==True:
                    shutil.rmtree(workspace_filename)  #if it exists, delete the save directory with all the old files
            else:
                shutil.rmtree(workspace_filename)#overwrite autosave

    try: #will not work before file is selected
        Files.change_or_make_directory(workspace_filename,'python_files')
        import_filename=str(workspace_filename)+'_import_file_path.pickle'
        with open(import_filename,'wb') as output_file:
            pickle.dump(file_path,output_file)
    except:
        pass
    os.chdir(directory_name)
    if os.path.isfile('workspace_index.pickle'):
        with open('workspace_index.pickle','rb') as input_file:
            workspace_index=pickle.load(input_file)
        workspace_index.append(workspace_filename)
        with open('workspace_index.pickle','wb') as output_file:
            pickle.dump(workspace_index,output_file)
    else:
        workspace_index.append(workspace_filename)
        with open('workspace_index.pickle','wb') as output_file:
            pickle.dump(workspace_index,output_file)
    try:
        file_access_window.destroy()
    except:
        pass
    

def load_workspace():
    global workspace_index
    workspace_listbox=Listbox(file_access_window)
    workspace_listbox.grid(row=1,column=1,padx=20,pady=5)
    if os.path.isfile('workspace_index.pickle'):
        with open('workspace_index.pickle','rb') as input_file:
            workspace_index=pickle.load(input_file)
            workspace_index=set(workspace_index) #remove duplicate workspace name entries
            workspace_index=list(workspace_index)
    for workspace in workspace_index:
        if os.path.isdir(workspace):
            workspace_listbox.insert(0,workspace)
    open_workspace_button=Button(file_access_window,text='Open',command=open_workspace)
    open_workspace_button.grid(row=2,column=1,padx=5,pady=5)
    open_workspace_button.config(state=DISABLED)


    def select_workspace(event):
        global workspace_filename
        workspace_listbox=event.widget
        index = int(workspace_listbox.curselection()[0])
        workspace_filename=workspace_listbox.get(index)
        open_workspace_button.config(state=NORMAL)
    
    workspace_listbox.bind('<<ListboxSelect>>', select_workspace)

def open_workspace():
    global new_workspace
    global file_path
    global imported_segmented_volume
    Files.change_and_check_directory(workspace_filename)
    check_imported=os.path.isdir('imported_segmented')
    if check_imported:
        imported_segmented_volume=True
        

    Files.change_and_check_directory(workspace_filename,'python_files')
    import_filename=str(workspace_filename)+'_import_file_path.pickle'

    
    with open(import_filename,'rb') as input_file:
        file_path=pickle.load(input_file)

    os.chdir(directory_name)
    new_workspace=False
    file_access_window.destroy()


#STATEMENTS#########################################################################################################################
if __name__ == "__main__":
    file_access_window=Tk()
    file_access_window.title('Contour v1.0')
    new_workspace_name=Entry(file_access_window,width=20)
    new_workspace_name.grid(row=1,column=0,padx=20,pady=5,sticky=N)
    new_workspace_name.insert(0,'autosave')
    def get_filename_and_save():
        global workspace_filename
        global new_workspace
        new_workspace=True
        workspace_filename=str(new_workspace_name.get())
        save_workspace(overwrite_query=True)
    
    def import_segmented_volume():
        global file_path
        global new_workspace
        file_path = filedialog.askopenfilename()
        get_filename_and_save()
        global imported_segmented_volume
        imported_segmented_volume=True
        new_workspace=False



    new_workspace_button=Button(file_access_window,text='New workspace',command=get_filename_and_save)
    new_workspace_button.grid(row=0,column=0,padx=20,pady=20)
    load_workspace_button=Button(file_access_window,text='Load workspace',command=load_workspace)
    load_workspace_button.grid(row=0,column=1,padx=20,pady=20)
    import_segmented_volume_button=Button(file_access_window,text='Import segmented volume',command=import_segmented_volume)
    import_segmented_volume_button.grid(row=2,column=0,padx=20,pady=20)

    def show_file_access_info():
        message='''
Workspaces are created and saved in 
{0}

To create a new workspace, enter a desired filename or use 'autosave' and click on New workspace. You can also overwrite exisiting workspaces.

The imported image should be 8-bit. To convert the image, open it in Fiji, and then go to Image > Type > 8-bit. Save it without overwriting the original file.

You can load a workspace you have already created from the drop-down list.

If you created a segmented volume using another segmentation tool, you can import it directly in order to quantitate the elements.
'''+str(email_string)
        message=message.format(directory_name)
        messagebox.showinfo(title='Workspace',message=message)

    file_access_info_button=Button(master=file_access_window,text='i',width=3,command=show_file_access_info)
    file_access_info_button.grid(row=3,column=1,padx=5,pady=5,sticky=E)

    def close_program():
        sys.exit()
    
    file_access_window.protocol("WM_DELETE_WINDOW", close_program)
    file_access_window.mainloop()

    import_window=Tk()
    import_window.title('Imported Image')
    preview_window=Toplevel()
    preview_window.title('Preview Segmentation')
    log_window=Tk()
    log_window.title('Log')
    log_window.resizable(width=False,height=False)
    log_window_progress_bar=LogWindow(master=log_window)
    LogWindow.create_log()
    log_window_progress_bar.hide_z_progress()
    segmented_vol_segmented_window=Toplevel() #Toplevel is used when functions occur between different Tk windows
    segmented_vol_segmented_window.title('Segmented Volume')
    volume_feature='Segmented_Vol'
    the_segment=SegmentedArray(image_array=None,master=segmented_vol_segmented_window,volume_feature=volume_feature)
    group_window=Toplevel()
    group_window.title('Quantitation')


    import_window.withdraw()
    preview_window.withdraw()
    

    log_window.withdraw()
    segmented_vol_segmented_window.withdraw()
    group_window.withdraw()

    if new_workspace: #i.e. if a workspace hasn't been loaded so we've got to start a new workspace
        file_path = filedialog.askopenfilename()


    preview_window.deiconify()
    import_window.deiconify()
    log_window.deiconify()
    
    if not imported_segmented_volume:
        source_image_stack=Window(master=import_window,filename=file_path)
        source_image_stack.process_image()
        source_image_stack.display_image(current_z) #at the start, current_z is set to the middle slice using the Window class initialiser
        source_image_stack.display_scroll_bar(initial=True)
        source_image_stack.display_stack_extremes(import_window)
        Histogram.display_blank_histogram(import_window)
        Histogram.display_histogram_limits(import_window)

        preview=PreviewWindow(master=preview_window,filename=file_path)
        preview.display_image(current_z) #at the start, current_z is set to the middle slice using the Window class initialiser
        preview.display_scroll_bar(initial=True)
        preview.display_stack_extremes(preview_window)
        Rangegram.display_blank_rangegram(preview_window)
        Rangegram.display_rangegram_limits(preview_window)
        if isinstance(rangegram_data,Rangegram):
            rangegram.bind('<Motion>',rangegram_data.select_boundary)

        save_workspace(overwrite_query=False)


        bind_collect_pixels()

        lock_buttons=LockPreview(source_window=import_window,target_window=preview_window)
        
        preview_button=Button(preview_window,text='Preview',command=PreviewWindow.enable_preview_button)
        preview_button.grid(row=1,column=11,padx=5,pady=5,sticky=N)

        segmented_vol=SegmentationButtons(master=import_window,volume_feature='Segmented_Vol',color='magenta',order='3')
        segmented_vol.display_buttons()
    else: 
        ##########IMPORT SEGEMENTED VOLUME################
        source_image_stack=Window(master=import_window,filename=file_path)
        source_image_stack.process_image()

        current_time=time.localtime()
        time_barcode='_'+str(current_time.tm_year)+'_'+str(current_time.tm_mon)+'_'+str(current_time.tm_mday)+'_'+str(current_time.tm_hour)+str(current_time.tm_min)+str(current_time.tm_sec)
        Files.change_or_make_directory(workspace_filename,'log_files')
        logging.basicConfig(filename='Log_'+str(workspace_filename)+time_barcode+'.log', format='%(asctime)s %(message)s', filemode='w')
        logger=logging.getLogger() 
        logger.setLevel(logging.INFO)
        LogWindow.update_log(workspace_filename)
        for line in message_template.splitlines():
            LogWindow.update_log(line)

        for z in range(0,len(stack)):
            stack[z].image_array=np.where(stack[z].image_array==0,0,1)
            stack[z].image_array=np.array(stack[z].image_array,dtype='uint8')
        
        
        Files.change_and_check_directory(workspace_filename)
        Files.change_and_overwrite_directory('imported_segmented',parent_directory=False)

        z_index=0
        for z in range(0,len(stack)):
            string_z_pos=StringZ.int_to_3_dec_string(z_index)
            disp_image=Image.fromarray(stack[z].image_array)
            disp_image.save(string_z_pos+'.tif')
            z_index=z_index+1
        
        segmented_vol_segmented_view=SegmentedView('imported_segmented',master=segmented_vol_segmented_window,volume_feature=volume_feature,\
                RGBA=(255,0,255,255),column=1)
        LogWindow.update_log('Assembling segmentation...')
        segmented_vol_segmented_view.display_image(z_slice=current_z)
        segmented_vol_segmented_view.display_scroll_bar(initial=True)
        segmented_vol_segmented_view.display_stack_extremes()
        segmented_vol_segmented_view.display_stack_button()
        segmented_vol_segmented_view.display_layer_button()
        segmented_vol_segmented_view.display_edit_buttons()
        
        import_window.withdraw()
        preview_window.withdraw()
        ################################################################

    def ask_quit_program():
        quit_box=messagebox.askyesno(title='Quit program?',message='Do you want to quit the program?')
        if quit_box:
            sys.exit()

    def hide_log_window():
        ask_quit_program() #this won't work if placed within try/except
        try:
            log_window.withdraw()
        except:
            pass


    def hide_segmented_vol_segmented_window():
        ask_quit_program()
        try:
            segmented_vol_segmented_window.withdraw()
        except:
            pass
    
    def hide_group_window():
        ask_quit_program()
        try:
            group_window.withdraw()
        except:
            pass
    

    
    def open_segmented_vol_segmentation():
        if not new_workspace:
            try:
                LogWindow.update_log(str(directory_name)+'/'+str(workspace_filename)+'/segmented_volume')
                global segmented_vol_segmented_view
                segmented_vol_segmented_view=SegmentedView(str(directory_name)+'/'+str(workspace_filename)+'/segmented_volume',master=segmented_vol_segmented_window,volume_feature='Segmented_Vol',\
                    RGBA=(255,0,255,100),column=1)
                segmented_vol_segmented_view.display_image(z_slice=current_z)
                segmented_vol_segmented_view.display_scroll_bar(initial=True)
                segmented_vol_segmented_view.display_stack_extremes()
                segmented_vol_segmented_view.display_stack_button()
                segmented_vol_segmented_view.display_layer_button()
                segmented_vol_segmented_view.display_edit_buttons()
            except:
                pass

    if not imported_segmented_volume:
        current_time=time.localtime()
        time_barcode='_'+str(current_time.tm_year)+'_'+str(current_time.tm_mon)+'_'+str(current_time.tm_mday)+'_'+str(current_time.tm_hour)+str(current_time.tm_min)+str(current_time.tm_sec)
        Files.change_or_make_directory(workspace_filename,'log_files')
        logging.basicConfig(filename='Log_'+str(workspace_filename)+time_barcode+'.log', format='%(asctime)s %(message)s', filemode='w')
        logger=logging.getLogger() 
        logger.setLevel(logging.INFO)
        LogWindow.update_log(workspace_filename)
        for line in message_template.splitlines():
            LogWindow.update_log(line)

        open_segmented_vol_segmentation()




    
    import_window.protocol("WM_DELETE_WINDOW", close_program)
    preview_window.protocol("WM_DELETE_WINDOW", close_program)
    log_window.protocol("WM_DELETE_WINDOW", hide_log_window)
    segmented_vol_segmented_window.protocol("WM_DELETE_WINDOW",hide_segmented_vol_segmented_window)
    group_window.protocol("WM_DELETE_WINDOW",hide_group_window)

    import_window.mainloop()
    preview_window.mainloop()
    selection_window.mainloop()
    segmented_vol_segmented_view.mainloop()
    group_window.mainloop()