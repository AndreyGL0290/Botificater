import pymorphy2 as pmr
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker
import copy

def name_change(name):

    morph = pmr.MorphAnalyzer(lang='ru') # определение пола
    maker = PetrovichDeclinationMaker()  # склонение ФИО
    full_name = name.split()  # разбиение ФИО на составляющие
    print(name, full_name)
    first_name = ''  # возможное имя
    sur_name = ''  # возможное фамилия
    patronymic = ''  # возможное отчество
    full_name_change = copy.deepcopy(full_name) 
    for elem in full_name_change:
        is_name = any('Name' in p.tag for p in morph.parse(elem))
        if is_name:
            first_name = elem
            full_name_change.remove(elem)
            break
    for elem in full_name_change:
        is_name = any('Surn' in p.tag for p in morph.parse(elem))
        if is_name:
            sur_name = elem
            full_name_change.remove(elem)
            break
    for elem in full_name_change:
        is_name = any('Patr' in p.tag for p in morph.parse(elem))
        if is_name:
            patronymic = elem
            full_name_change.remove(elem)
            break
    
    final_name = ""
    cased_first_name = cased_sur_name = cased_patronymic = ''
    gender = ""
    if first_name:
        if 'masc' in morph.parse(first_name)[0].tag:
            gender = Gender.MALE
        elif 'femn' in morph.parse(first_name)[0].tag:
            gender = Gender.FEMALE
        cased_first_name = maker.make(NamePart.FIRSTNAME,gender, Case.DATIVE, first_name)
        
    if sur_name:
        if 'masc' in morph.parse(sur_name)[0].tag:
            gender = Gender.MALE
        elif 'femn' in morph.parse(sur_name)[0].tag:
            gender = Gender.FEMALE
        cased_sur_name = maker.make(NamePart.FIRSTNAME,gender, Case.DATIVE, sur_name)

    if patronymic:
        if 'masc' in morph.parse(patronymic)[0].tag:
            gender = Gender.MALE
        elif 'femn' in morph.parse(patronymic)[0].tag:
            gender = Gender.FEMALE
        cased_patronymic = maker.make(NamePart.FIRSTNAME,gender, Case.DATIVE, patronymic)

    print()
    print(final_name)
    print()
    if len(full_name_change) != 0:
        for elem in full_name:
            gender = ''
            if 'masc' in morph.parse(elem)[0].tag:
                gender = Gender.MALE
            elif 'femn' in morph.parse(elem)[0].tag:
                gender = Gender.FEMALE
            print("Гендер:", gender)
            is_name = any('Name' in p.tag for p in morph.parse(elem))
            is_patronymic = any('Patr' in p.tag for p in morph.parse(elem))
            is_sur_name = any('Surn' in p.tag for p in morph.parse(elem))
            if is_sur_name:
                cased_last_name = maker.make(NamePart.LASTNAME, gender, Case.DATIVE, elem)
                final_name += ' ' + cased_last_name
            elif is_name:
                cased_name = maker.make(NamePart.FIRSTNAME,gender, Case.DATIVE, elem)
                final_name += ' ' + cased_name
            elif is_patronymic:
                cased_patronymic = maker.make(NamePart.MIDDLENAME, gender, Case.DATIVE, elem)
                final_name += ' ' + cased_patronymic
            else:
                final_name += elem
        final_name = final_name.strip()
        print("Итог: ", final_name)
    else:
        final_name = cased_sur_name + ' ' + cased_first_name + ' ' + cased_patronymic
        final_name = final_name.strip()

    return final_name


    
    

'''
    f_name = ''
    print()
    print(morph.parse(name))
    for elem in morph.parse(name):
        print(elem)
        if 'Patr' in elem.tag:
            f_name = elem
    print()

    is_name = any('Patr' in p.tag for p in morph.parse(name))
    print(is_name)
    print("Ok")
'''

'''
    if 'masc' in morph.parse(full_name[1])[0].tag:
        gender = Gender.MALE
    else:
        gender = Gender.FEMALE
    
    if 'masc' in morph.parse(full_name[1])[0].tag:
        cased_last_name = maker.make(NamePart.LASTNAME, Gender.MALE, Case.DATIVE, full_name[0])
        cased_name = maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.DATIVE, full_name[1])
    elif 'femn' in morph.parse(full_name[1])[0].tag:
        cased_last_name = maker.make(NamePart.LASTNAME, Gender.FEMALE, Case.DATIVE, full_name[0])
        cased_name = maker.make(NamePart.FIRSTNAME, Gender.FEMALE, Case.DATIVE, full_name[1])
    try:
        if 'masc' in morph.parse(full_name[1])[0].tag:
            cased_middle_name = maker.make(NamePart.MIDDLENAME, Gender.MALE, Case.DATIVE, full_name[2])
            print("Hi", cased_middle_name)
        elif 'femn' in morph.parse(full_name[1])[0].tag:
            cased_middle_name = maker.make(NamePart.MIDDLENAME, Gender.FEMALE, Case.DATIVE, full_name[2])

        return [cased_last_name, cased_name, cased_middle_name]
    except IndexError:
        return [cased_last_name, cased_name, '']
'''