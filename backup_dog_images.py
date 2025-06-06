import os
import json
import requests
from tqdm import tqdm


# Ссылки на API
DOG_API_BASE = "https://dog.ceo/api" 
YA_DISK_API = "https://cloud-api.yandex.net/v1/disk/resources" 
HEADERS_TEMPLATE = lambda token: {"Authorization": f"OAuth {token}"}


def get_breed_subbreeds(breed):
    """Получает список подпород для указанной породы."""
    response = requests.get(f"{DOG_API_BASE}/breed/{breed}/list")
    if response.status_code != 200:
        return []
    return response.json().get("message", [])


def get_breed_image_urls(breed, subbreeds):
    """Получает ссылки изображений для основной породы и всех подпород.
    Берёт по одному изображению на каждую подпороду и одно для основной породы."""
    image_urls = {}

    # Изображение для основной породы
    response = requests.get(f"{DOG_API_BASE}/breed/{breed}/images/random")
    if response.status_code == 200:
        url = response.json()["message"]
        filename = f"{breed}_{os.path.basename(url)}"
        image_urls[filename] = url

    # По одному изображению для каждой подпороды
    for sub in subbreeds:
        response = requests.get(f"{DOG_API_BASE}/breed/{breed}/{sub}/images/random")
        if response.status_code == 200:
            url = response.json()["message"]
            filename = f"{breed}_{sub}_{os.path.basename(url)}"
            image_urls[filename] = url

    return image_urls


def create_folder_on_ya_disk(token, folder_name):
    """Создает папку на Я.Диске."""
    headers = HEADERS_TEMPLATE(token)
    params = {"path": folder_name}
    response = requests.put(f"{YA_DISK_API}", headers=headers, params=params)
    if response.status_code not in (201, 409):  # 409 — папка уже существует
        raise Exception(f"Ошибка при создании папки: {response.text}")


def upload_file_to_ya_disk(token, file_name, file_url, folder_name):
    """Загружает файл напрямую на Я.Диск."""
    headers = HEADERS_TEMPLATE(token)
    params = {
        "url": file_url,
        "path": f"{folder_name}/{file_name}",
        "disable_redirects": True
    }
    response = requests.post(f"{YA_DISK_API}/upload", headers=headers, params=params)
    if response.status_code != 202:
        raise Exception(f"Ошибка загрузки файла {file_name}: {response.text}")


def save_json_report(data, filename="result.json"):
    """Сохраняет информацию о загруженных файлах в JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    breed = input("Введите название породы на английском: ").strip().lower()
    token = input("Введите токен с  Полигона Я.Диска: ").strip()

    print(f"\nПолучаем информацию о породе '{breed}'")
    subbreeds = get_breed_subbreeds(breed)

    print(f"Найдено подпород: {len(subbreeds)}")
    image_urls = get_breed_image_urls(breed, subbreeds)

    if not image_urls:
        print("Не удалось получить изображения.")
        return

    folder_name = breed.capitalize()
    print(f"\nСоздаём папку '{folder_name}' на Я.Диске")
    create_folder_on_ya_disk(token, folder_name)

    print("\nЗагружаем изображения на Я.Диск")
    results = []

    for filename, url in tqdm(image_urls.items(), desc="Загрузка файлов", total=len(image_urls)):
        upload_file_to_ya_disk(token, filename, url, folder_name)
        results.append({"file_name": filename})

    save_json_report(results)
    print("\nВсе файлы успешно загружены!")
    print(f"Результат сохранён в файл 'result.json'")


if __name__ == "__main__":
    main()