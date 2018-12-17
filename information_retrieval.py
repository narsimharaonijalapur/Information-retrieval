
# coding: utf-8

# In[92]:


import re
import glob
import pandas as pd
import numpy as np
import PyPDF2
import roman
from tabula.wrapper import read_pdf
import spacy


def pdf_text_pre_processor(header, text):

    ''' This function takes the heading and text from pdf and returns required preprocessed text for further process.

    Parameters:

    header(str): The heading of interest

    text(str): Any text data which is in string format

    returns:

    preprocessed_text(str): Required preprocessed text from pdf

    '''

    temp = re.sub(r'\n|Section \d{1,2}|Note \d{1,2}|\.[0-9][0-9] '+ header + '|\.[0-9] ' + header , '' , str(text)) 
    temp = re.sub(r'Notes \d{1,2}', 'Notes', temp) 
    temp = re.sub(r'Method ' + header + '|Accuracy, '+ header + '|' + header.upper(), header, temp)
    temp = re.sub(r'\)', ' ', temp) 
    pre_processed_text = re.sub(r'\(', ' ', temp)

    return pre_processed_text


def pdf_processor(file_path, header):

    '''This function takes the file path and header as inputs and returns heading start , end patterns 
    and also preprocessed text by calling pdf_text_pre_processor().

    Parameters:

    file_path(str): Path to read a pdf file from a directory.

    header(str): The heading of interest

    returns:

    preprocessed_text(list): Required preprocessed text from pdf

    start(str): Start pattern of the header, the text under which we are interested in

    end(str): End pattern of the header,the text under which we are interested in

    pdf_name(str): filename or the DOWID of the document (without file extension)

    corpus(object): PyPDF2.corpus object file can be used to read the pdf later

    header(str): String pattern of the header, for example 'Precision'

    pages(number): total number of pages in the document

    '''

    pdf_name = file_path.split('/')[-1].split('\\')[-1].split('.')[0]

    corpus = PyPDF2.PdfFileReader(file_path)

    pages = corpus.getNumPages()

    preprocessed_text = [pdf_text_pre_processor(header, corpus.getPage(page_num).extractText()) for page_num in range(0, pages)]

    text = ' '.join(preprocessed_text)

    if all([header not in text for text in preprocessed_text]):
        start, end = np.nan, np.nan

    else:
        start = re.search(r'[0-9][0-9] '+ header +'|[0-9] ' + 
                          header + '|[0-9][0-9].' + header + 
                          '|[0-9].' + header + '|[0-9][0-9]. ' + 
                          header + '|[0-9]. ' + header + '|[0-9][0-9].  ' +  
                          header + '|[0-9].  ' + header , text)

        if(start == None):
            start, end = np.nan, np.nan


        else:

            if '.' in start.group(0):
                start1 = start.group(0).split('.')[0]
                end = str(int(start1) + 1) + "\."

            else:
                start1 = start.group(0).split(' ')[0]
                end = str(int(start1) + 1) + " "

            start = start.group(0)

    return preprocessed_text, start, end, pdf_name,corpus,header,pages


# In[4]:


def text_data(preprocessed_text, start, end):
    '''This is a function that returns the text in between the given start and end patterns.

    Parameters:

    preprocessed_text(list): The list of preprocessed text in a list

    start(str): This is a start pattern 

    end (str): This is an end pattern

    Returns:

    text_between(str): The output is the text between the given patterns

    ''' 
    text_between=''
    if str(start) != 'nan':
        text = ' '.join(preprocessed_text)
        end1= re.sub(r'\\\.','',end)
        pattern1 = r'' + start + "(.+?)" + end + "\s*[A-Z]"
        pattern2 = r'' + start + "(.+?)" + end1 + "\s+[A-Z]"
        pattern3 = r'' + start + "(.+?)" + end + "\s*[a-z]"
        pattern4 = r'' + start + "(.+?)" + "THE INFORMATION HEREIN"
        pattern5 = r'' + start + "(.+?)" + "The information herein"
        pattern6 = r'' + start + "(.+?)" + "Appendix"
        patterns= [pattern1,pattern2,pattern3,pattern4,pattern5,pattern6]

        for pattern in patterns:
            temp = re.findall(pattern,text)
            if temp!=[]:
                text_between = temp[0]
                break
        return text_between



def tabula_table_generator(file, start_page, pdf_name_data, pdf_name_count, page_break_count):

    '''This function generates the list of tables from the pages where required heading (like 'Precision') data presented in pdf

    Parameters:

    file(str): filename or the DOWID of the document

    start_page(number): Page number of pdf from where heading (like 'Precision') data started

    pdf_name_data(list): This is the set of pdf id along with some texts presented in the extracted heading text

    pdf_name_count(number): Count that represents how many times the pdf name occurred in the extracted heading text

    page_break_count(number): Count of pages having required heading (like 'Precision') data

    returns:

    tabledata(list): List of tables presented in the pages of pdf in which required heading (like 'Precision') data presented

    '''

    tabledata = []

    if (pdf_name_data != []) and (pdf_name_count != 0):
        new_pages = str(str(start_page + 1) + "-" + str(start_page + pdf_name_count + 1))

    elif page_break_count!= 0:
        new_pages = str(str(start_page + 1) + "-" + str(start_page + page_break_count + 1))

    else:     
        new_pages = str(start_page + 1)

    tabledata = read_pdf(file, output_format = "dataframe", pages = new_pages, lattice=True,
                         multiple_tables = True, encoding = 'latin-1', position = "absolute")

    if tabledata == []:
        tabledata = read_pdf(file, output_format = "dataframe", pages = new_pages, lattice = False,
                             multiple_tables = True, encoding = 'latin-1', position = "absolute")

    return tabledata


def string_comp_match(text_between, tabledata):

    '''This is a function that returns the tables which are having the information provided in the required text data.

    Parameters:
    text_between(str): The text in between the start and end patterns in the text of the pdf

    tabledata(list): The list of table data sets which are in the pdf

    Returns:

    tabledata(list): List of table data sets in which the table values matched with text between start and end patterns. 

    '''

    final_table = []
    textdata1 = re.sub(r"\n\s+|TM", "", str(text_between))
    textdata1 = re.sub(r"[^0-9a-zA-Z]+", "", str(textdata1))       
    for i in range(0, len(tabledata)):
        tabledata1 = tabledata[i].dropna(how='all')
        temp_table = tabledata1.values
        for row in range(2, len(temp_table)):
            string = str(temp_table[row])
            string = re.sub(r"\\r|nan|NaN|[^0-9a-zA-Z]+|TM","", string)
            string = string.replace("x80x9c","")
            string = string.replace("x80x93","")

            if string in textdata1:
                final_table = final_table + [tabledata1]
                break
    return final_table



def table_data(file, preprocessed_text, text_between, pdf_name, start, header):

    '''

    file(str): filename or the DOWID of the document

    preprocessed_text(list): Whole pdf text data which is already pre processed 

    text_between(str): The text in between the start and end patterns in the text of the pdf

    pdf_name(str): filename or the DOWID of the document (without file extension)

    start(str): Start pattern of the header, the tables under which we are interested in

    header(str): String pattern of the header, for example 'Precision'

    '''
    tabledata=[]
    if str(start) != 'nan':
        ##finding pagebreaks in the pdf
        pages = len(preprocessed_text)
        pattern = "Page \d{1,2} of " + str(pages)
        page_break = re.findall(pattern, str(text_between))
        page_break_count = len(page_break)
        pattern = pdf_name + "(.+?)"
        pdf_name_data = re.findall(pattern, str(text_between))
        pdf_name_count = str(text_between).count(str(pdf_name))

        for i in range(0, pages): 
            temp = preprocessed_text[i]
            if start in str(temp):
                tabledata1 = tabula_table_generator(file, i, pdf_name_data, pdf_name_count, page_break_count) 
                tabledata1 = string_comp_match(text_between, tabledata1)
                if tabledata1 != []:
                    tabledata = tabledata+[tabledata1]       
        return tabledata



def out_tables_list(text_between):

    '''This function takes the text between start and end patterns of heading as input and returns 
    the list of table names referenced in the text but presented some where else in pdf.

    Parameters:

    text_between(str): The text in between the start and end patterns in the text of the pdf

    returns:

    table_start_list(list): List of tables referenced in the heading (like 'Precision') text

    table_end_list(list): List of table names which are expected as the end patterns for table_start_list

    '''

    integers = list(range(1,50))
    roman_num = list(range(1,50))

    for integer in range(0, len(roman_num)):
        roman_num[integer] = roman.toRoman(int(roman_num[integer]))

    table_start, table_start1, table_end, table_end1="","","",""  
    textdata_temp = str(text_between).split(" ")       

    for word in range(0,len(textdata_temp)):    
        textdata_temp[word]=re.sub('\'|\"|\,|\.|\\\\|\[|\]',"",textdata_temp[word])

        for number in range(0, len(roman_num)):

            if textdata_temp[word] == roman_num[number] or textdata_temp[word]==str(integers[number]) and "ble" in textdata_temp[word-1]:   
                table_start=table_start+",Table "+roman_num[number]    
                table_end=table_end+",Table "+roman_num[number+1]    
                table_start1=table_start1+",Table "+str((integers[number]))    
                table_end1=table_end1+",Table "+str(integers[number+1])

    table_start=pd.DataFrame(table_start[1:len(table_start)].split(","))[0].unique() 
    table_start1=pd.DataFrame(table_start1[1:len(table_start1)].split(","))[0].unique()  
    table_end=pd.DataFrame(table_end[1:len(table_end)].split(","))[0].unique()     
    table_end1=pd.DataFrame((table_end1[1:len(table_end1)].split(",")))[0].unique()

    table_start=table_start+","+table_start1
    table_end=table_end+","+table_end1

    for tablename in range(0,len(table_start)):     
        table_start[tablename]=table_start[tablename].split(",")
        table_end[tablename]=table_end[tablename].split(",")

    table_start=re.sub(r'\)|\(|\[|\]|\'',"",str(table_start))    
    table_start=re.sub(r'list|\n',",",str(table_start))    
    table_start=re.sub(r"\s*T|\s*able \d{1,2}T",'T',str(table_start))   
    table_start=re.sub(r"\s\,",',',str(table_start))   
    table_start_list=table_start.split(",")[1:len(table_start)]
    table_end=re.sub(r'\)|\(|\[|\]|\'',"",str(table_end))
    table_end=re.sub(r'list|\n',",",str(table_end))
    table_end=re.sub(r"\s*T",'T',str(table_end)) 
    table_end=re.sub(r"\s\,",',',str(table_end))
    table_end_list=table_end.split(",")[1:len(table_end)]

    return table_start_list,table_end_list



def out_tables(file,text_between,preprocessed_text,header,corpus,pages,table_start_list,table_end_list):

    '''This takes table names list as input and returns the tables related to the table names list.

    Parameters:

    file(str): filename or the DOWID of the document

    text_between(str): The text in between the start and end patterns in the text of the pdf

    preprocessed_text(list)e pdf text data which is already pre processed 

    header(str):String pattern of the header, for example 'Precision'

    corpus(object): PyPDF2.corpus object file can be used to read the pdf later

    pages(number): total number of pages in the document

    table_start_list(list): List of tables referenced in the heading (like 'Precision') text

    table_end_list(list): List of table names which are expected as the end patterns for table_start_list

    returns:

    tabledata(list): List of tables presented in the pages of pdf in which required heading (like 'Table I') data presented.

    '''

    tabledata=[]
    remove_text=r"\.\.|following tab|table(|s) be|Metablen|in the table(|s)(|\.)|(T|t)able(|s) (be|of)|[a-z][a-z]table|table according"
    textdata=re.sub(remove_text,"",str(text_between))

    preprocessed_text1=(re.sub(r'see Appendix|'+remove_text,"",temp) for temp in preprocessed_text)

    if " Table " or " table " or " tables " or " Tables " or " TABLE " or " TABLES " in str(textdata):
        table_start_list,table_end_list=out_tables_list(text_between)

        if table_end_list!=['', ' ']:

            table_start=re.search("Table(|s)\s*\-*\s*\w*",str(text_between))

            if table_start!=None:
                j=0
                find=''
                find_list=['THE IFORMATION HEREIN','THE INFORMATION HEREIN','The information herein','Appendix']
                text_at_end=''   
                for word in range(0,len(find_list)):

                    for page in range(0,len(preprocessed_text)):

                        if find_list[word] in preprocessed_text[page]:
                            tablepage=page
                            text_at_end=preprocessed_text[tablepage:len(preprocessed_text)]
                            find=find_list[word]
                            break

                if find!='' and table_start!=' ' or '':

                    for table in range(0,len(table_start_list)):                        
                        table_start=table_start_list[table]
                        table_end=table_end_list[table]

                        if str(table_end) in str(text_at_end):
                            pattern=str(table_start)+"(.+?)"+str(table_end)

                        else:
                            table_end=str(text_at_end)[len(str(text_at_end))-8:len(str(text_at_end))]
                            pattern=str(table_start)+"(.+?)"+table_end

                        text_between=str(re.findall(pattern,str(text_at_end)))

                        for k in range(tablepage,len(preprocessed_text)):

                            if table_start in preprocessed_text[k]:
                                new_pages=str(k+1)+"-"+str(k+2)
                                if k+1==pages:
                                    new_pages=str(pages) 
                                tabledata=read_pdf(file,output_format="dataframe",pages=new_pages,lattice=True,
                                                   multiple_tables=True,encoding = 'latin-1',position="absolute")
                        tabledata = string_comp_match(text_between=str(text_at_end),tabledata=tabledata)

                        if tabledata !=[]:
                            break
    return tabledata


def value_unit_spacy(text_data):
    '''To extract the value and unit of the precision in text_data
    Parameters:
    text_data(str): The extracted data under precision

    Returns:
    value(int): The precision value
    unit(str): The unit type of precision value
    len_value(int): Number of precision values in the text_data'''




    nlp=spacy.load("./text_final_1")

    value_unit=[]
    value_list=[]
    unit_list=[]

    define_words = 'standard'
    match_sentence =re.findall(r"([^.]*?%s.*?\.)(?!\d)" % define_words,str(text_data))
    doc_value_unit=nlp(str(match_sentence))

    for ent in doc_value_unit.ents:
        if ent.label_=='value_unit':
            value_unit.append(ent.text)
            value_unit=''.join(value_unit)
            value_temp=re.findall(r'(\d+?\.*\d*)',value_unit)
            unit_temp=re.sub(r'\d+?\.*\d*',"",value_unit)

            if '/' in str(unit_temp) and len(value_temp)>1:
                uni=unit_temp.split('/')
                val_1=value_temp
                value_temp=value_temp[0]
                unit_temp=str(uni[0]+'/'+str(val_1[1]+unit_temp[1]))
            value_list.append(value_temp)    
            unit_list.append(unit_temp)    
            value_unit=[]

    if value_list==[]:
        value_list.append("No Value")

    if unit_list==[]:
        unit_list.append("No Unit")

    value=pd.Series(value_list)
    unit=pd.Series(unit_list)

    temp_unit=re.search(r'wt\.(.+?)(\.|\%)',str(text_data))
    if temp_unit != None and "wt/wt" not in str(text_data):
        temp_unit=temp_unit.group(0)
        for uni_1 in range(0,len(unit)):
            unit[uni_1]=temp_unit

    len_value=len(value)        

    return value,unit,len_value



def precision_type_spacy(text_data):
    '''To extract the precision type 
    Parameters:
    text_data(str): The extracted data under precision

    Returns:
    precision_type(str): List of precision types for the precision values'''

    precision_type=[]

    type_list=['relative','absolute','pooled','arelative']

    define_words = 'standard'
    match_sentence =re.findall(r"([^.]*?%s.*?\.)(?!\d)" % define_words,str(text_data))
    match_precision_type= re.findall(r'((?:\w+\s+){0,2}\bstandard\b\s*(?:\w+\s+){0})',str(match_sentence))
    for match in match_precision_type:
        temp=match.split( )
        if len(temp) !=1 and temp[1] != 'ASTM':
            if ((temp[0] in type_list) and (temp[1] in type_list)):
                precision_type.append(temp[0]+temp[1])
            elif temp[1] in type_list:
                if temp[1]=='pooled':
                    temp[1]='pooled absolute'
                if temp[1]=='arelative':
                    temp[1]='relative'
                precision_type.append(temp[1])
            else:
                precision_type.append('nan')   

    if precision_type==[]:
        precision_type.append("No Precision type")
    precision_type_list=pd.Series(precision_type)   
    precision_type_list=precision_type_list.replace('nan','absolute')

    length_value=value_unit_spacy(text_data)[2]

    precision_type_list=precision_type_list.tolist()
    if length_value==2 and len(precision_type_list)==1:
        precision_type_list.extend([0] * (length_value-1))
        precision_type_list[1]=precision_type_list[0]

    precision_type_list=pd.Series(precision_type_list)

    return precision_type_list


def distribution_spacy(text_data):
    '''To extract the distribution of the component(s) or matrix 
    Parameters:
    text_data(str): The extracted data under precision

    Returns:
    distribution: List of distribution(s) for the component(s) or matrix'''


    nlp=spacy.load("./text_model_1")

    distribution=[]

    length_value=value_unit_spacy(text_data)[2]
    match_distribution = re.findall(r'((?:\w+\s+){0,5}\bnormal\b\s*(?:\S+\s+){1})',str(text_data))

    for dist in range(0,len(match_distribution)):
        if match_distribution[dist] == 'did not originate from a normal distribution.  ':
            match_distribution[dist]='assumes a non- normal distribution'

    doc_distribution=nlp(str(match_distribution))

    for ent in doc_distribution.ents:
        distribution.append(ent.text)

    if len(distribution)==0:
        distribution.append('normal(if null)')

    if length_value>1 and len(distribution)==1:
        distribution.extend([0] * (length_value-1))
        for d in range(0,len(distribution)-1):
            distribution[d+1]=distribution[d]

    distribution=pd.DataFrame(distribution,columns=['dist'])    

    list1=['Assuming normal distribution ','normal distributions','assumes a normal distribution','assumes a normal','assumes a non- normal','assumes a non- normal distribution','assumed to be normal','Assuming a normal distribution']
    list2=['assumed normal','normal distribution','assumed normal','assumed normal','unknown','unknown','non','assumed normal']
    distribution.replace(list1,list2,inplace=True)
    distribution=[x for x in distribution['dist'] if str(x) != 'non']
    distribution=pd.Series(distribution)

    value=value_unit_spacy(text_data)[0]
    value_list=pd.Series(value)
    frames=[distribution,value_list]
    distribution_df=pd.concat(frames,axis=1)
    distribution_df.columns=['distribution','value']

    if len(distribution)>=len(value_list):
        count=len(distribution)
    elif len(value_list)>len(distribution):
        count=len(value_list)

    for i in range(0,count):        
        if len(distribution)>=len(value_list) and i<(len(distribution)-1):
            if distribution_df["distribution"].iloc[i-1]=='assumed normal' and distribution_df['distribution'].iloc[i]=='normal distribution':
                distribution_df['distribution'].iloc[i-1]='normal distribution'    
            if distribution_df["distribution"][0]=='assumed normal' and distribution_df['distribution'][1]=='normal distribution':
                distribution_df['distribution'][0]='normal distribution'

        if len(value_list)>len(distribution):
            distribution_df.replace(np.nan,"non",inplace=True)
            for k in range(0,len(distribution_df)):
                if distribution_df['distribution'][k]=="non":
                    distribution_df['distribution'].iloc[k]=distribution_df['distribution'].iloc[k-1]

    distribution=distribution_df['distribution']

    return distribution


def condition_spacy(text_data):
    '''To extract the condition of the component(s) 
    Parameters:
    text_data(str): The extracted data under precision

    Returns:
    condition: List of condition(s) for the component(s)'''

    con = []
    condition = []
    nlp = spacy.load("./text_final_1")
    doc_con=nlp(text_data)
    for ent in doc_con.ents:
        if ent.label_=='condition':
            con.append(ent.text)
#     print('condition \n',con,'\n\nlength of condition\n',len(con),'\n\nlength of value:\n',len(value))
    if len(con)==4 and con[0]=='Repeatability':
        con[0]=con[0]+" "+(con[1])
        con[2]=con[2]+" "+con[3]
        del con[1]
        del con[2]

    len_of_value=value_unit_spacy(text_data)[2]
    if len_of_value>len(con):
        con.extend([0] * (len_of_value-1))
        for x in range(0,len(con)-1):
            con[x+1]=con[x]

    if con==[]:
        con.append("No Condition Given")
    temp_unit=re.search(r'wt\.(.+?)(\.|\%)',str(text_data))
    if temp_unit != None: 
        temp_con=re.search(r'\s*an\s*average(.+?)\.\s*\%(.+?)\.',str(text_data))
        if temp_con != None:
            temp_con=temp_con.group(0)
            con=temp_con
    condition=pd.Series(con)

    return condition


def component_matrix(scope_text,precision_data,precision_text,test_pdf):
    nlp=spacy.load("./scope_model_1")
    test_pdf = test_pdf.replace("./data/","")
    data = pd.DataFrame()
    text ="[  "+test_pdf+"  HEADING and SCOPE:  "+scope_text+"]  PRECISION:  ["+ precision_text+"  ]" 
    doc = nlp(text)
    component_precision,component_scope,matrix=[],[],[]
    for ent in doc.ents:
#         print(ent.text,ent.label_)
        if ent.label_ == "component_precision":
            component_precision.append(ent.text)
        if ent.label_ == "component_scope":
            component_scope.append(ent.text)
        if ent.label_ == "matrix":
            matrix.append(ent.text)
    lengths = [len(matrix),len(component_precision),len(component_scope)]
    if len(precision_data) == len(component_scope):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(component_scope)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['matrix'][i] =matrix
            data['component'][i] = component_scope[i]
    elif len(precision_data) == len(component_precision):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(component_precision)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['matrix'][i] =matrix
            data['component'][i] = component_precision[i]
    elif len(precision_data) == len(matrix):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(matrix)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['component'][i] =component_precision
            data['matrix'][i] = matrix[i]
    elif len(component_precision) == len(component_scope):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(component_scope)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['matrix'][i] =matrix
            data['component'][i] = component_scope[i]
    elif len(component_precision) < len(component_scope):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(component_scope)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['matrix'][i] =matrix
            data['component'][i] = component_scope[i]
    elif len(component_precision) > len(component_scope):
        data = pd.DataFrame(columns = ["filename",'matrix','component'],index = range(0,len(component_precision)))
        for i in range(0,len(data)):
            data['filename'][i] = test_pdf
            data['matrix'][i] =matrix
            data['component'][i] = component_precision[i]
    return data


def precision_dataframe_spacy(text_data,test_pdf):
    '''To get a dataframe returning precision value, unit, precision_type, distribution
    Parameters:
    text_data(str): The extracted data under precision

    Returns:
    data: A dataftrame with columns of value,unit,precision_type,distribution
    value: List of precision value(s)
    unit: List of unit(s) of precision value(s)
    precision_type: List of precision types for the precision value(s)
    distribution: List of distribution(s) for the component(s) or matrix'''
    dowid=[]    
    col=col=['Dow_id','precision','unit','distribution','precision_type']
    data=pd.DataFrame(columns=col)

    value=value_unit_spacy(text_data)[0]
    unit=value_unit_spacy(text_data)[1]
    prec_type=precision_type_spacy(text_data)
    dis=distribution_spacy(text_data)
    len_of_val=value_unit_spacy(text_data)[2]
    id1=re.sub(r'\/home/cdsw/data/MethodsForSoothsayer_181105/','',test_pdf)
    condition = condition_spacy(text_data)

    data_frame={'precision': pd.Series(value),'unit': pd.Series(unit), 'precision_type': pd.Series(prec_type),'distribution':pd.Series(dis),'condition':condition}
    data_frame =pd.DataFrame(data_frame)
    dataframe_final=data_frame.dropna()
    frames=[data,dataframe_final]
    data=pd.concat(frames,axis=0)
    data.index=range(0,len(data))
    for i in range(0,len(data)):
        dowid.append(id1)
    data['Dow_id']=dowid

    return data

def final_scope(test_pdf,precision_data,precision_text):

    tabledata=[]
    table_data1=[]
    scope_data = "This is tabledata"
    data = pd.DataFrame(columns = ["filename",'matrix','component'])
    preprocessed_text, start, end, pdf_name,corpus,header,pages=pdf_processor(file_path=test_pdf, header="Scope")
    text_between=text_data(preprocessed_text, start, end)
    scope_text = text_between
    tabledata1=table_data(test_pdf, preprocessed_text, text_between, pdf_name, start, header)
    table_start_list,table_end_list=out_tables_list(text_between)
    out_tabledata=out_tables(test_pdf,text_between,preprocessed_text,header,corpus,pages,table_start_list,table_end_list)

    if preprocessed_text.count('  ')==len(preprocessed_text):
        scope_data="Input file is in Image format"

    elif str(start)=='nan':
        scope_data="No "+header+" data in input file"

    else:

        if tabledata1 !=[] and out_tabledata!=[]:
            scope_data=[]
            tabledata=tabledata+[tabledata1]
            scope_data=tabledata+[out_tabledata]
        elif out_tabledata!=[]:
            scope_data=[]
            scope_data=out_tabledata
        elif tabledata1!=[]:
            scope_data=[]
            scope_data=tabledata1
        elif tabledata1==[] and text_between != '':
            scope_data=text_between
            scope_text=text_between
    data = component_matrix(scope_text,precision_data,precision_text,test_pdf)

    return scope_data,data



def final_precision(test_pdf):

    tabledata=[]
    table_data1=[]
    text_between = ''
    precision_data = "This is table data"
    data = "This is tabledata"
    final_data = "This is tabledata"
    preprocessed_text, start, end, pdf_name,corpus,header,pages=pdf_processor(file_path=test_pdf, header="Precision")
    text_between=text_data(preprocessed_text, start, end)
    tabledata1=table_data(test_pdf, preprocessed_text, text_between, pdf_name, start, header)
    table_start_list,table_end_list=out_tables_list(text_between)
    out_tabledata=out_tables(test_pdf,text_between,preprocessed_text,header,corpus,pages,table_start_list,table_end_list)

    if preprocessed_text.count('  ')==len(preprocessed_text):
        precision_data="Input file is in Image format"

    elif str(start)=='nan':
        precision_data="No "+header+" data in input file"

    else:

        if tabledata1 !=[] and out_tabledata!=[]:
            precision_data=[]
            tabledata=tabledata+[tabledata1]
            precision_data=tabledata+[out_tabledata]
        elif out_tabledata!=[]:
            precision_data=[]
            precision_data=out_tabledata
        elif tabledata1!=[]:
            precision_data=[]
            precision_data=tabledata1
        elif tabledata1==[] and text_between != '':
            precision_text= text_between
            precision_data=precision_dataframe_spacy(text_between,test_pdf)
            precision_data.index=range(0,len(precision_data)) 
            scope_data,data = final_scope(test_pdf,precision_data,precision_text)
            frames = [precision_data['Dow_id'],data['matrix'],data['component'],precision_data.drop('Dow_id',axis=1)]
            final_data = pd.concat(frames,axis=1)
            final_data = final_data.fillna(" ")  

    return precision_data,data,final_data


####Code for table  metadata
def final_table(tabledata):
    final_tabledata =pd.DataFrame(columns=['Dow_id','matrix','component','precision','unit','precision_type','distribution','condition'])

    for table in range(0,len(tabledata[0])):

        data = tabledata[0][table]
        data.columns = data.iloc[0]
        data =data.drop(0,0).reset_index().drop('index',1)
        final_data = pd.DataFrame(columns=['Dow_id','matrix','component','precision','unit','precision_type','distribution','condition'],index=range(0,len(data)))

        precision_list = ['precision','standarddeviation',"standardvalue"]
        condition_list = ['averangeconcentration','average']
        component_list = ['sample','analyte','resin','analysis','resin#']
        actual_columns = data.columns

        columns = []
        for i in range(0,len(data.columns)):
            columns.append(re.sub(r"\r|\s","",str(data.columns[i])).lower())
        data.columns =columns
        cols=[]
        if str(data.columns).count("standarddeviation")>1:
            for i in range(0,len(data.columns)):
                col=data.columns[i]
                if "standarddeviation" in col and col != "standarddeviation":
                    cols.append(col)
        data = data.drop(cols,1)
        for col in data.columns:
            if "95%confidence" in col:
                data = data.drop(col,1)

        for k in range(0,len(final_data)):
            final_data["component"][k]=re.sub(r"\r"," ",str(data[data.columns[0]][k]))

        for k in range(0,len(final_data)):
            final_data["matrix"][k] = data.columns[0].upper()
        for col in data.columns:
            if "distribution" in col:
                for k in range(0,len(final_data)):
                    final_data["distribution"][k]=col
            else:
                for k in range(0,len(final_data)):
                    final_data["distribution"][k]= "normal(if Null)"
        for col in data.columns:
            for name in precision_list:
                if name in col:
                    if col == "standarddeviation":
                        for k in range(0,len(final_data)):
                            final_data["precision_type"][k]="absolute"
                        for k in range(0,len(final_data)):
                            final_data["precision"][k]=data[col][k]
                    else:
                        temp = re.sub(r"standarddeviation","",col)
                        if len(temp) < 2:
                            temp = "absolute"
                        for k in range(0,len(final_data)):
                            final_data["precision_type"][k]=temp
                        for k in range(0,len(final_data)):
                            final_data["precision"][k]=data[col][k]

            precision_unit = final_data['precision'].values
            precision_unit = re.search(r"\[(.+?)\]",str(precision_unit))
            if precision_unit != None:
                precision_unit = precision_unit.group(0)
                precision_unit = re.sub(r"(N|n)ote(s|)|\d|\.|\\r|\'|\[|\]|\(|\)","",str(precision_unit))
            for k in range(0,len(final_data)):
                final_data['unit'][k] = precision_unit

            for name in condition_list:
                if name in col:
                    for k in range(0,len(final_data)):
                        final_data["condition"][k]=data[col][k]
                    condition_unit = final_data['condition'].values
                    condition_unit = re.search(r"\[(.+?)\]",str(condition_unit))
                    if condition_unit != None:
                        condition_unit = condition_unit.group(0)
                        condition_unit = re.sub(r"\d|\.|\\r|\'|\[|\]","",str(condition_unit))
                    for k in range(0,len(final_data)):
                        final_data["condition"][k]= str(final_data['condition'][k]) + " " +str(condition_unit)+" " + str(col)

        final_data = final_data.drop(0,0)
        final_tabledata = pd.concat([final_tabledata,final_data],axis=0)
        final_tabledata.index = range(0,len(final_tabledata))
        for k in range(0,len(final_tabledata)):
            final_tabledata['Dow_id'][k] = re.sub(r"\/home/cdsw/data/MethodsForSoothsayer_181105/","",test_pdf)

    return final_tabledata


# In[114]:


import os
os.getcwd()
os.chdir("/home/cdsw/Dow_Codes")

test_pdf="./data/101500-TE94A.pdf"

precision_data,data,final_data=final_precision(test_pdf)
final_data


# In[115]:


columns_list = ['Dow_id', 'matrix', 'component', 'condition', 'distribution','precision_type', 'unit', 'precision']
meta_df = pd.DataFrame(columns = columns_list)
count =0
globaldata = glob.glob("/home/cdsw/data/MethodsForSoothsayer_181105/*.pdf")
for pdf in range(0,100):
    test_pdf = globaldata[pdf]
    print("Document Number ----",pdf+1)
    precision_data,data,final_data=final_precision(test_pdf)

    if str(type(final_data)) == "<class 'pandas.core.frame.DataFrame'>":
        count=count+1
        print(test_pdf,count)
        frames = [meta_df,final_data]
        meta_df = pd.concat(frames,axis=0)
meta_df.index = range(0,len(meta_df))


# In[117]:


pdfs = ['102375-E18F.pdf','102170-E11B.pdf','102755-E14A.pdf','102727-E17A.pdf','101212-E17D.pdf','101567-ME97B.pdf','102176-E06A.pdf']
table_dataframe = pd.DataFrame(columns=['Dow_id','matrix','component','precision','unit','precision_type','distribution','condition'])
for pdf in range(0,len(pdfs)):
    test_pdf = "/home/cdsw/data/MethodsForSoothsayer_181105/"+pdfs[pdf]
    preprocessed_text, start, end, pdf_name,corpus,header,pages=pdf_processor(file_path=test_pdf, header="Precision")
    text_between=text_data(preprocessed_text, start, end)
    tabledata=table_data(test_pdf, preprocessed_text, text_between, pdf_name, start, header)
    final_tabledata = final_table(tabledata)
    table_dataframe = pd.concat([table_dataframe,final_tabledata],axis=0)
    table_dataframe.index = range(0,len(table_dataframe))


# In[120]:


data = pd.concat([meta_df,table_dataframe],axis=0)
data.index = range(0,len(data))
data['average'] = " "
data = data[['Dow_id','matrix','component','average','precision','precision_type','unit','distribution','condition']]
data.to_csv("demo_output_dataframe.csv",index=False)

