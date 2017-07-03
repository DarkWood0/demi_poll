from grab import Grab
import os
import json
import re
import urllib.request

g = Grab()

# Ссылку можно ввести по запросу скрипта в консоли или непосредственно здесь
# Если хотите использовать ссылку внутри скрипта,
# то закомментируйте (добавьте один или два символа "#") первую строку url
# и разкомментируйте вторую
# В таком случае ссылку следует вставлять между кавычками
url = input('Введите полную ссылку на тему, для которой хотите создать голосование (http://...): ')
##url = ''

login_url = url.split('?')[0] + '?'
gallery_url = login_url + 'act=module&module=gallery&cmd=user&user=2&op=topic_images&topic=' + url.split('=')[1]

# Авторизуемся на форуме
g.go(login_url)
g.doc.set_input('UserName', 'Ваш_логин')
g.doc.set_input('PassWord', 'Ваш_пароль')
g.doc.submit()

# Список страниц темы
theme_pagination = []
# Список страниц галереи
gallery_pagination = []
# Список пользователей
usernames = []
# Список ссылок на изображения в теме
all_image_links = []
# Список ссылок на изображения в галерее
# Используется для сравнения с длиной списка изображений темы
# и удаления несоответствующих картинок из того же списка
# Обусловлено такое поведение алгоритмом определения первого
# уникального для каждого пользователя файла, загруженного на форум
# в конкретную тему
image_links_gallery = []

def get_data(url):
    """Получает имя пользователя и соответствующую ему ссылку на изображение
из самой темы"""
    # Изображения
    images = g.doc.select("//div[@class='postspace2']//img")
    for image in images:
        selection = image.select("@src").text()
        all_image_links.append(selection)
    # Пользователи
    users = g.doc.select("//span[@class='thumb_name'][2]")
    for user in users:
        selection = user.text()
        usernames.append(selection)

def get_pages(url, output_list, k=0):
    """Получает страницы для темы и для галереи"""
    # Если страниц больше одной, то формируются ссылки на них,
    # которые добавляются в соответствующий список
    # Скрипт проверяет есть ли в данной теме пагинация (страницы)
    g.go(url)
    pages = g.doc.select("//table[@class='iptable']/tr/td/span/a")
    if pages.exists() == True: 
        if len(pages.text()) > 19:
            raise Exception("Слишком много страниц для обработки")
        elif len(pages.text()) > 16:
            kp = pages.text()[-3:]
        elif len(pages.text()) > 15:
            kp = pages.text()[-2:]
        elif len(pages.text()) == 15:
            kp = pages.text()[-1]
        for page in range(0, int(kp)):
            if output_list == theme_pagination:
                k = 15
                page = page*k
            elif output_list == gallery_pagination:
                k = 30
                page = page*k
            output_list.append(url + '&st=' + str(page))
        # Обрабатываются все найденные страницы
        for page in output_list:
            g.go(page)
            get_data(page)
    # Если страницы одна, то она не добавляется в список пагинации,
    # а сразу обрабатывается
    else:
        g.go(url)
        get_data(url)

def get_data_gallery():
    """Получает имя пользователя и соответствующую ему ссылку на изображение
в галерее темы"""
    # Скрипт выделяет область с именем пользователя и ссылкой на изображение
    user_images = g.doc.select("//div[@class='thumb-cell-pad']")    
    # Здесь получает ссылки на изображения
    for image in user_images:
        selection = image.select(
            "div[@class='wraptocenter']/a/img[@class='shadow']").select(
                '@src').text()
        image_links_gallery.append(selection)

def filter_images(input_list):
    """Фильтрует все полученные из темы изображения по признаку их загрузки
на форум"""
    filtered_image = filter(demi_image.match, input_list)
    output_list = list(filtered_image)
    return output_list

# Запуск функции для получения страниц темы
get_pages(url, theme_pagination)
# Для получения страниц галереи
get_pages(gallery_url, gallery_pagination)

# Сортировка списка картинок при помощи созданной выше функции filter_images
demi_image = re.compile(r'.*demiart\.ru/forum/uploads.*')
demi_image_links = filter_images(all_image_links)

# В этом блоке объявляются переменные для хранения полученных данных
# Во всех ссылках используется принцип "%номер_темы%_%название_папки_и_файла%"
#
#
#
unique_images = 'downloaded_images/' + url.split('=')[1] + '_unique/unique_matching.txt'
all_images = 'downloaded_images/' + url.split('=')[1] + '_all/all_matching.txt'
store_data = 'downloaded_images/data/' + url.split('=')[1] + '_data_state.json'
data_folder = os.path.dirname(store_data)

def ensure_dir(directory):
    """Проверяет существование указанной папки.
Если таковая отсутствует - создает ее."""
    if not os.path.exists(directory):
        os.makedirs(directory)

# Убеждаемся в существовании папки для хранения данных, благодаря которым
# в последующих запусках скрипт будет ориентироваться была ли добавлена
# новая информация в указанную вами тему или нет
ensure_dir(data_folder)

# Блок проверки длин списков с именами пользователей и
# фильтрованных изображений из темы
# Если эти значения несовпадают, то запускается процесс сравнения
# списка картинок из темы и из галереи
# Найденные в списке из темы исключения удаляются (иначе неправильно
# сработает алгоритм определения первого для каждого пользователя файла

if len(usernames) == len(demi_image_links):
    current_state = len(usernames)
else:
    for page in theme_pagination:
        g.go(page)
        get_data_gallery()
    with open(data_folder + '/'+ url.split('=')[1] + '_theme_images.json', 'w') as file:
        json.dump(demi_image_links, file)
    with open(data_folder + '/' + url.split('=')[1] + '_gallery_images.json', 'w') as file:
        json.dump(image_links_gallery, file)
    with open(data_folder + '/' + url.split('=')[1] + '_gallery_images.json') as file:
        gallery = json.load(file)
    with open(data_folder + '/' + url.split('=')[1] + '_theme_images.json') as file:
        theme = json.load(file)
    while len(theme) != len(gallery):
        for item in theme:
            if item not in gallery:
                theme.remove(item)
    current_state = len(usernames)

# Создается база данных (в данном случае в виде словаря,
# в которой и происходит определение первых для каждого пользователя файлов
database = dict(zip(usernames[::-1], demi_image_links[::-1]))

def file_directory(filename):
    """Получает имя файла и возвращает из него директорию назначения"""
    directory = os.path.dirname(filename)
    return directory

def clear_dir(directory):
    """Удаляет файлы из указанной директории.
!Важно! Применять после проверки папки на существование (функция ensure_dir)
и перед записью в нее новых файлов"""
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

# Следующая функция сохраняет текущую длину списка пользователей,
# на которую скрипт будет ориентироваться на последующих запусках
def save_data(filename):
    """Сохраняет текущее состояние списка пользователей"""
    with open(filename, 'w') as f_obj:
        json.dump(current_state, f_obj)

def downloading(data_object, directory):
    """Сохраняет изображения из data_object в directory"""
    for link in data_object:
        image_name = link.rsplit('/',1)[1]
        print('Загружается изображение ' + image_name)
        urllib.request.urlretrieve(link, directory + '/' + image_name)

def write_to_file(filename, data_object):
    """Записывает соответствие имен пользователей и загруженных ими изображений
в указанный файл. data_object должен быть словарем"""
    for name, link in data_object:
        prepared_links = link + ' ' + name[2:]
        with open(filename, 'a') as output:
            output.write(prepared_links + '\n')

def get_all_matching(usernames, image_links):
    """Получает соответствие всех имен пользователей с загруженными ими
изображениями; передаваемые аргументы должны быть списками"""
    matching = []
    for i in range(max((len(usernames),len(image_links)))):
        while True:
            data = (usernames[i],image_links[i])
            matching.append(data)
            break
    return matching

# По сути основная функция скрипта, в которой применяются созданные выше функции
def print_matching(filename, user_list, image_list, data_object):
    """Запрашивает у пользователя дальнейшие действия; в зависимости от выбора
скачивает изображения и распечатывает соответствие их с именами пользователей
или только скачивает"""
    directory = file_directory(filename)
    ensure_dir(directory)
    clear_dir(directory)
    q_print = input('Хотите распечатать соответствие имен и ссылок? (y/n): ')
    if q_print == 'y':
        if filename == all_images:
            downloading(image_list, directory)
            write_to_file(filename, get_all_matching(user_list, image_list))
        elif filename == unique_images:
            downloading(list(data_object.values()), directory)
            write_to_file(filename, data_object.items())
    elif q_print == 'n':
        if filename == all_images:
            downloading(image_list)
        elif filename == unique_images:
            downloading(list(data_object.values()))

# В этой функции обрабатывается ваш выбор: уникальные картинки или все
# В функции print_images происходит направление данных в нужную папку согласно
# переденному аргументу (имени файла)
def check_data_store(data_file=store_data):
    """Проверяет наличие хранилища данных для конкретной темы,
если таковое отсутствует, то создает его"""
    try:
        with open(data_file) as f_obj:
            old_state = json.load(f_obj)
    except FileNotFoundError:
        save_data(data_file)        
        question = """Что вы хотите сделать?
    1) Скачать уникальные изображения
    2) Скачать все изображения
Введите номер пункта: """
        active = True
        while active:
            choose = input(question)
            if choose == '1':
                print_matching(unique_images, usernames, demi_image_links, database)
                active = False
            elif choose == '2':
                print_matching(all_images, usernames, demi_image_links, database)
                active = False
            else:
                print('Такого пункта не существует! Попробуйте еще раз.\n')
    else:
        return old_state

# Данная функция сверяет равенство старых данных с новыми для конкретной темы
# Если они равны, то выдается сообщение "Нет новых данных", если есть -
# запускается процесс их обработки
# Вы снова получаете запрос: "Скачать уникальные изображения?.."
# Это будет происходить только для новых данных

# На всякий случай добавлена проверка от уменьшения счетчика новых сообщений
# Если он по какой-то причине станет больше текущего состояния (иными словами,
# текущее состояние будет меньше), то скрипт выдаст соответствующую ошибку
def check_data_state(old_state=check_data_store()):
    """Сверяет равенство старых данных с новыми для конкретной темы"""
    if old_state == current_state:
        print("Нет новых данных")
    elif old_state > current_state:
        raise Exception("счетчик новых сообщений " +
                        "не может иметь отрицательное значение!")
    else:
        user_copy = usernames[:]
        user_copy.clear()
        for user in usernames[old_state:]:
            user_copy.append(user)
        image_copy = demi_image_links[:]
        image_copy.clear()
        for image in demi_image_links[old_state:]:
            image_copy.append(image)
        database_copy = dict(zip(user_copy[::-1], image_copy[::-1]))        
        question = """Что вы хотите сделать?
    1) Скачать уникальные изображения
    2) Скачать все изображения
Введите номер пункта: """
        active = True
        while active:
            choose = input(question)
            if choose == '1':
                print_matching(unique_images, user_copy, image_copy, database_copy)
                active = False
            elif choose == '2':
                print_matching(all_images, user_copy, image_copy, database_copy)
                active = False
            else:
                print('Такого пункта не существует! Попробуйте еще раз.\n')
        save_data(store_data)
        
# При первом запуске скрипта перехватывает ошибку, инициируемую
# функцией check_data_state() потому, что необходимый ей для работы
# файл еще не создан. Он будет доступен только при последующих запусках
def first_start():
    try:
        check_data_state()
    except TypeError:
        pass
    
first_start()
