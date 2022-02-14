import pymorphy2 as pmr
from pytrovich.enums import Gender

morph = pmr.MorphAnalyzer(lang="ru")

name_list = [
"Александра Горащенко FEMALE",
"Евгений Пономорев MALE",
"Александр Глухов MALE",
"Юлий Цезарь MALE",
"Федор Бондарчук MALE",
"Евгения Путилина FEMALE",
'Юлия Еремеева FEMALE',
'Федора Печкина FEMALE',
"Мишель Сорокина FEMALE",
'Мишель Стоунс MALE',
'Мирослава Тихомолова FEMALE'
]
print(morph.parse("пропимарт"))
for i in name_list:
    j = morph.parse(i.split()[0])
    for ii in range(len(j) - 1):
        if {'masc', 'nomn'} in j[ii].tag:
            gender = Gender.MALE
            break
        elif "masc" in j[ii].tag:
            gender = Gender.FEMALE
            break
        elif {'femn', 'nomn'} in j[ii].tag:
            gender = Gender.FEMALE
            break
        elif "femn" in j[ii].tag:
            gender = Gender.MALE
            break
    print(i, gender)