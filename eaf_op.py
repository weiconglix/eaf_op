# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 10:05:01 2019

@author: WL
"""

import pympi    # Import pympi to work with elan files
import os
import re
import pandas as pd

def get_parent_tier_list(eaf_obj,filename='this'):
    """
    get independant tier list from elan object
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object, elan file object created using pympi-ling
        ex: import pympi
            eaf_obj = pympi.Elan.Eaf(r'C:\1.eaf')
    Optional arguments:
        :param str filename: filename of the eaf object, for error display only
    """
    parent_tier_list = eaf_obj.get_tier_ids_for_linguistic_type('default', parent=None)
    if not parent_tier_list:
        parent_tier_list = eaf_obj.get_tier_ids_for_linguistic_type('default-lt', parent=None)
        if not parent_tier_list:
            parent_tier_list = eaf_obj.get_tier_ids_for_linguistic_type('praat', parent=None)
            if not parent_tier_list:
                print(filename + " file does not have default or default-lt tier")          
    return parent_tier_list

def add_child_tier(eaf_obj, parent_tier, child_tier_prefix):
    """
    create child tier having similar name as parent tier
        ex: parent_tier: sd@spk, child_tier: ex@spk, utt@spk, phon@spk 
            
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object
    :param str parent_tier: name of the parent tier
    :param str child_id_prefix: prefix of the child tier name, if the child exists, this will do nothing
    """
    child_tier = child_tier_prefix + parent_tier[parent_tier.index('@'):] # tier name: extra@xxx
    if child_tier not in eaf_obj.get_child_tiers_for(parent_tier):
        eaf_obj.add_tier(child_tier, parent=parent_tier, ann=None)

def del_child_tier(eaf_obj, parent_tier, child_tier_prefix):
    """
    delete child tier having similar name as parent tier
        ex: parent_tier: sd@spk, child_tier: ex@spk, utt@spk, phon@spk 
            
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object
    :param str parent_tier: name of the parent tier
    :param str child_id_prefix: prefix of the child tier name, if child_tier does not exist, this will do nothing
    """
    child_tier_list = eaf_obj.child_tiers_for(parent_tier)
    child_tier = child_tier_prefix + parent_tier[parent_tier.index('@'):]          
    if child_tier in child_tier_list:
        eaf_obj.remove_tier(child_tier)
    
def del_identical_annotation_in_child_tier(eaf_obj, parent_tier, child_tier_prefix):
    """
    compare child tier against parent tier, and delete identical annotation in child tier  
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object
    :param str parent_tier: name of the parent tier
    ::param str child_id_prefix: prefix of the child tier name, child tier can be created using: add_child_tier(eaf_obj, parent_tier, child_tier_prefix)
    """
    par = eaf_obj.tiers[parent_tier]
    child_tier_list = eaf_obj.child_tiers_for(parent_tier)
    child_tier = child_tier_prefix + parent_tier[parent_tier.index('@'):]
    if child_tier in child_tier_list:
        chi = eaf_obj.tiers[child_tier]
        for chi_aid in chi[1]:
            token = chi[1][chi_aid]
            par_aid = token[0]
            if par_aid in par[0]:
                if chi[1][chi_aid][1] == par[0][par_aid][2]: # compare strings
                    chi[1][chi_aid] = tuple((token[0],'',token[2],token[3])) # make it blank

def move_annotation_to_child_tier(eaf_obj, parent_tier, child_tier_prefix, regex, copyflag=1):
    """
    use regular expression to search particular annotation in parent tier and move them into child tier
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str parent_tier: name of the parent tier for searching particular annotation
    :param str child_id_prefix: prefix of the child tier name, child tier can be created using: add_child_tier(eaf_obj, parent_tier, child_tier_prefix)
    :param str regex: regular expression for searching particular annotation
    :param int coypflag: 0->move annotation (original anno in parent tier will be deleted), 1->copy annotation (origianl annoation in parent tier will remain)
    """
    par = eaf_obj.tiers[parent_tier]
    child_tier_list = eaf_obj.child_tiers_for(parent_tier)
    child_tier = child_tier_prefix + parent_tier[parent_tier.index('@'):]
    if child_tier in child_tier_list:
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            # find target annotation
            target_anno = re.findall(regex, anno)
            if target_anno:
                # copy annotation to child tier
                eaf_obj.add_ref_annotation(child_tier, parent_tier, eaf_obj.timeslots[token[0]], target_anno[0])  # token[0]: start time
                # remove origianl annotation in parent tier
                if copyflag == 0:
                    anno = anno.replace(target_anno[0], '')
                    par[0][aid] = tuple((token[0], token[1], anno, token[3]))
                    
def replace_annotation_by_dict(eaf_obj, tier, dictionary):
    """
    replace particular annotation defined by dictionary(case sensitive) WL comment: need to add option for case insensitive
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str tier: name of the targe tier for searching particular annotation
    :param dict dictionary: python dictionary object
    
    """
    if eaf_obj.tiers[tier][0]: # parent tier
        par = eaf_obj.tiers[tier]
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            anno_pattern = re.compile(r'\b(' + '|'.join(dictionary.keys()) + r')\b') # replace content that has word boundary
            anno = anno_pattern.sub(lambda x: dictionary[x.group()], anno)
            par[0][aid] = tuple((token[0], token[1], anno, token[3]))
    elif eaf_obj.tiers[tier][1]: # child tier 
        chi = eaf_obj.tiers[tier]
        for aid in chi[1]:   
            token = chi[1][aid]
            anno = token[1]     
            anno_pattern = re.compile(r'\b(' + '|'.join(dictionary.keys()) + r')\b') # replace content that has word boundary
            anno = anno_pattern.sub(lambda x: dictionary[x.group()], anno)
            chi[1][aid] = tuple((token[0], anno, token[2], token[3]))

def replace_annotation(eaf_obj, tier, regex, new_content):
    """
    find particular annotation using regular expression and replace with new_content
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str tier: name of the targe tier for searching particular annotation
    :param str regex: regular expression for searching particular annotation
    :param str new_content: replaced new content
    
    """
    if eaf_obj.tiers[tier][0]: # parent tier
        par = eaf_obj.tiers[tier]
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            anno = re.sub(regex, new_content, anno)
            par[0][aid] = tuple((token[0], token[1], anno, token[3]))
    elif eaf_obj.tiers[tier][1]: # child tier 
        chi = eaf_obj.tiers[tier]
        for aid in chi[1]:   
            token = chi[1][aid]
            anno = token[1]      
            anno = re.sub(regex, new_content, anno)
            chi[1][aid] = tuple((token[0], anno, token[2], token[3]))
            
def generate_excel(table, filename=r'output_table.xlsx', sort_by=None):
    """
    writes an excel file from a pandas DataFrame, if the excel file exists, then append
    
    :param table: pandas object
    Optional arguments:
        * filename (including path)
        * sort_by: column to sort, if None no sorting is done
    """
    if sort_by is not None:
        table = table.sort_values(by=sort_by)
    if os.path.exists(filename): # if exist, append
        exst_sheet = pd.ExcelFile(filename).parse() # read spreadsheet
        exst_sheet = exst_sheet.append(table)
    else:
        exst_sheet = table
    exst_sheet.to_excel(filename, engine='openpyxl', index=False) # export to a spreadsheet file (xlsx) under corpus_root folder

def search_output_annotation(eaf_obj, tier, regex, eaf_name, output_file='output_table.xlsx'):
    """
    use regular expression to search particular annotation in parent tier and export into excel spreadsheet
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str tier: name of the parent tier for searching particular annotation
    :param str regex: regular expression for searching particular annotation
    :param str eaf_name: elan file name
    :param str output_file: whole path of the output_file
    """
    content_tab=[('fileName','tierName','start (s)','annotation','target')]
    if eaf_obj.tiers[tier][0]: # parent tier
        par = eaf_obj.tiers[tier]   
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            # find target annotation
            target_annos = re.findall(regex, anno)
            if target_annos:
                for target_anno in target_annos:
                    time_ref = token[0]
                    content_tab.append((eaf_name, tier, eaf_obj.timeslots
                                        [time_ref]/1e3, anno,target_anno)) # put them into a list; later export to a spreadsheet
    elif eaf_obj.tiers[tier][1]: # child tier 
        chi = eaf_obj.tiers[tier]
        parent_tier=chi[2]['PARENT_REF']
        par = eaf_obj.tiers[parent_tier]   
        for aid in chi[1]:   
            token = chi[1][aid]
            anno = token[1] 
            # find target annotation
            target_annos = re.findall(regex, anno)
            if target_annos:
                for target_anno in target_annos:
                    time_ref = par[0][token[0]][0]
                    content_tab.append((eaf_name, tier, eaf_obj.timeslots[time_ref]/1e3, anno,target_anno)) # put them into a list; later export to a spreadsheet    
    new_sheet = pd.DataFrame.from_records(content_tab[1:], columns=content_tab[0])
    generate_excel(new_sheet, filename=output_file, sort_by='start (s)')
    
def del_punctuation(eaf_obj, tier):
    """
    del all the punctuations in the specified tier but keep space, use this with care
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str tier: name of the targe tier for searching particular annotation
    
    """
    def del_punct(x):
        # remove symbols , ? . various dashes
        x = re.sub(r'([-–—\']+)', '', x) # if ? or - or en dash or em dash in the middle or alone, delete '
        x = re.sub(r'[,\?\.\!:;\"\&\$\%\^\*\+\=\\\|\/\(\)\[\]\{\}\<\>]+',' ', x) # replace other symbols with space                 
        # clean extra space
        x = " ".join(x.split()) # delete space at start and end, and extra space in the middle
        return x
    
    if eaf_obj.tiers[tier][0]: # parent tier
        par = eaf_obj.tiers[tier]
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            anno = del_punct(anno)
            par[0][aid] = tuple((token[0], token[1], anno, token[3]))
    elif eaf_obj.tiers[tier][1]: # child tier 
        chi = eaf_obj.tiers[tier]
        for aid in chi[1]:   
            token = chi[1][aid]
            anno = token[1]      
            anno = del_punct(anno)
            chi[1][aid] = tuple((token[0], anno, token[2], token[3]))

def del_punctuation_convert_initial_uppercase_to_lowercase(eaf_obj, tier, exception_list):
    """
    convert first capital letter to lowercase at start of sentence, but ignore words specified in exception_list
    
    :param pympi.Elan.Eaf eaf_obj: Target Eaf object.
    :param str tier: name of the parent tier for searching particular annotation
    :param str exception_list: name of the exception list containing the words that need to be skipped

    """
    def del_punct_convert(x):
        x = re.sub(r'(\b[,\?\.\!:]+)|([,\?\.\!:]+\b)', '\n', x) # if ? or , or . meets word boundary or nubmer, replace it with \n, after change uppercase, recover
        x = re.sub(r'([,\?\.\!\*]+)', '', x) # if ,or. stands by itself, delete
        x = re.sub(r'([-–—]+)', '', x) # if ? or - or en dash or em dash in the middle or alone, delete
        # cap table
        anno_temp=x.split('\n') # split at each utterance specified by . ? !
        for ind, single_anno in enumerate(anno_temp):
            single_anno=single_anno.strip()
            if single_anno and single_anno!=' ' and single_anno[0].isupper() and single_anno.split()[0] not in exception_list: # Initial word with first capital letter            
                anno_temp[ind] = single_anno[0].lower()+single_anno[1:] #first word of the 
        x = re.sub(r'\n', '', ' '.join(anno_temp)) 
        x = re.sub(r'[;\"\&\$\%\^\*\+\=\\\|\/\(\)\[\]\{\}\<\>]+',' ', x) # replace other symbols with space
        x = re.sub(r'[\']+','', x) # delete                    
        # clean space
        x = " ".join(x.split()) # delete space at start and end, and extra space in the middle
        return x
    
    if eaf_obj.tiers[tier][0]: # parent tier
        par = eaf_obj.tiers[tier]
        for aid in par[0]:   
            token = par[0][aid]
            anno = token[2]     
            anno = del_punct_convert(anno)
            par[0][aid] = tuple((token[0], token[1], anno, token[3]))
    elif eaf_obj.tiers[tier][1]: # child tier 
        chi = eaf_obj.tiers[tier]
        for aid in chi[1]:   
            token = chi[1][aid]
            anno = token[1]      
            anno = del_punct_convert(anno)
            chi[1][aid] = tuple((token[0], anno, token[2], token[3]))

    
    
    
    
    
    
    
    
    