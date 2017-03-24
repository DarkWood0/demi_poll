from grab import Grab
from operator import itemgetter
import os
import urllib.request

g = Grab()

# Ссылку можно ввести по запросу скрипта в консоли или непосредственно здесь
# Если хотите использовать ссылку внутри скрипта,
# то закомментируйте (добавьте один или два символа "#") первую строку url
# и разкомментируйте вторую
# В таком случае ссылку следует вставлять между кавычками
url = input('Введите полную ссылку на тему, для которой хотите создать голосование (http://...): ')
##url = 'http://demiart.ru/forum/index.php?showtopic=259709'

split_url = url.split('=')[1]
gallery_url = 'https://demiart.ru/forum/index.php?'
gallery_url += 'act=module&module=gallery&cmd=user&user=2&op=topic_images&topic='
parse_url = gallery_url + split_url

g.go(parse_url)

# Список страниц
pagination = []
# Список пользователей
usernames = []
# Список ссылок на изображения
image_links = []

def get_data():
    """Получает имя пользователя и соответствующую ему ссылку на изображение"""
    # Скрипт выделяет область с именем пользователя и ссылкой на изображение
    user_images = g.doc.select("//div[@class='thumb-cell-pad']")
    # Получает имена пользователей и добавляет в соответствующий список
    for user in user_images:
        selection = user.select("span[@class='thumb_name'][2]").text()
        usernames.append(selection)
    # Здесь получает ссылки на изображения
    for image in user_images:
        selection = image.select(
            "div[@class='wraptocenter']/a/img[@class='shadow']").select(
                '@src').text()
        image_links.append(selection)

# Скрипт проверяет есть ли в данной галерее изображений пагинация (страницы)
pages = g.doc.select("//*[@id='ucpcontent']/table/tr/td/span/a")

# Если страниц больше одной, то формируются ссылки на них,
# которые добавляются в соответствующий список
if pages.exists() == True:
    for page in range(0, int(pages.text()[-1])):
        page = page*30
        pagination.append(parse_url + '&st=' + str(page))
    # Обрабатываются все найденные страницы
    for page in pagination:
        g.go(page)
        get_data()
# Если страницы одна, то она не добавляется в список пагинации,
# а сразу обрабатывается
else:
    g.go(parse_url)
    get_data()

# Создается база данных (в данном случае в виде словаря)
# из имен пользователей и ссылок на изображения
database = dict(zip(usernames[::-1], image_links[::-1]))

# Полученная выше база сортируется по значению
# (для этого нужен импорт itemgetter из operator)
# itemgetter(1) - сортировка по значению
# itemgetter(0) - сортировка по ключу
# (необходим параметр reverse=True для сортировки по возрастанию (A-Z))
# Подробнее про такую сортировки смотрите PEP 265
sorted_database = sorted(database.items(), key=itemgetter(1), reverse=True)

unique_images_filename = 'downloaded_images/unique/unique_matching.txt'
unique_images_directory = os.path.dirname(unique_images_filename)
all_images_filename = 'downloaded_images/all/all_matching.txt'
all_images_directory = os.path.dirname(all_images_filename)

def ensure_dir(directory):
    """Проверяет существование указанной папки.
Если таковая отсутствует - создает ее."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_dir(directory):
    """Удаляет файлы из указанной директории.
!Важно! Применять после проверки папки на существование
и перед записью в нее новых файлов)"""
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def download_images(data_object, directory):
    """Скачивает изображения из указанного объекта (data_object),
который должен быть представлен списком"""
    ensure_dir(directory)
    clear_dir(directory)
    for link in data_object:
        image_name = link.rsplit('/',1)[1]
        print('Загружается изображение ' + image_name)
        urllib.request.urlretrieve(link, directory + '/' + image_name)
        
#__Загрузка уникальных изображений__
# альтернативный вариант без функции (для постоянного пользования только им)
##ensure_dir(unique_images_directory)
##clear_dir(unique_images_directory)
##for link in database.values():
##    image_name = link.rsplit('/',1)[1]
##    print('Загружается изображение ' + image_name)
##    urllib.request.urlretrieve(link, unique_images_directory + image_name)

#__Загрузка всех изображений__
# альтернативный вариант без функции (для постоянного пользования только им)
##ensure_dir(all_images_directory)
##clear_dir(all_images_directory)
##for link in image_links:
##    image_name = link.rsplit('/',1)[1]
##    print('Загружается изображение ' + image_name)
##    urllib.request.urlretrieve(link, all_images_directory + image_name)

##def clear_text_file(filename):
##    """Очищает текстовый файл перед записью в него новых данных"""
##    with open(filename, 'w') as clear_file:
##        clear_file.seek(0)
##        clear_file.truncate()

def write_to_file(filename, data_object):
    """Записывает данные в текстовый файл.
filename - имя файла, data_object - откуда извлекаются данные;
data_object - должен быть словарем"""
    for name, link in data_object:
        prepared_links = link + ' ' + name[2:]
        with open(filename, 'a') as output:
            output.write(prepared_links + '\n')

def get_all_matching():
    """Получает соответствие всех имен пользователей и ссылок
на загруженные ими изображения"""
    matching = []
    for i in range(max((len(usernames),len(image_links)))):
        while True:
            data = (usernames[i],image_links[i])
            matching.append(data)
            break
    return matching

def print_matching(filename):
    """Выводит в файл соответствие имен пользователей
и ссылок на загруженные ими изображения"""
    q_print = input('Хотите распечатать соответствие имен и ссылок? y/n ')
    if q_print == 'y':
        if filename == all_images_filename:
            write_to_file(filename, get_all_matching())
        else:
            write_to_file(filename, sorted_database)
    elif q_print == 'n':
        pass

# Скрипт спрашивает в консоли что вы будете делать
# Если введете 1, то скачаются уникальные изображения
# Если 2 - все
question = """Что вы хотите сделать?
    1) Скачать уникальные изображения
    2) Скачать все изображения
Введите номер пункта: """
active = True
while active:
    choose = input(question)
  
    if choose == '1':
        download_images(database.values(), unique_images_directory)
        print_matching(unique_images_filename)
        active = False
    elif choose == '2':
        download_images(image_links, all_images_directory)
        print_matching(all_images_filename)
        active = False
    else:
        print('Такого пункта не существует! Попробуйте еще раз.\n')
