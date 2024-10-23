workspace {
    name "FaceBook"
    description "Социальная сеть"
    
    model {
        user = person "Пользователь/Его стена" {
        }
        socialNetwork = softwareSystem "Социальная сеть" {
            description "Платформа для социального взаимодействия пользователей"

            frontend = container "Web Site" {
                description "Визуальный интерфейс"
                technology "HTML, CSS, JS"
            }

            user_api = container "API User changes" {
                description "API, балансировщик нагрузки"
                technology "Python"
            }

            business_api = container "API Business logic" {
                description "API, балансировщик нагрузки"
                technology "Python"
            }

            db = container "DataBase" {
                description "База данных общая"
                technology "PostgreSQL"
            }

        }


        user -> frontend "Использует"
        frontend -> user_api "Исполнение запросов изменения данных пользователя"
        frontend -> business_api "Исполнение запросов работы мессенджера"
        user_api -> db "Читает и записывает данные"
        business_api -> db "Читает и записывает данные"
    }

    views {

        dynamic socialNetwork "uc01" "Запросы к DB"{
            autoLayout lr
            frontend -> user_api "Создание нового пользователя"
            user_api -> db "POST/new_user/ {login:<>,password:<>}"

            frontend -> user_api "Поиск пользователя по логину"
            user_api -> db "GET/get_user/login=<>"

            frontend -> user_api "Поиск пользователя по маске имя и фамилии"
            user_api -> db "GET/get_user_by_name/name=<>,sername=<>"

            frontend -> user_api "Добавление записи на стену"
            user_api -> db "POST/create_post/ {login:<>, password:<>, content:<>}"

            frontend -> user_api "Загрузка стены пользователя"            
            user_api -> db "GET/get_user_wall/login=<>"

            frontend -> user_api "Отправка сообщения пользователю"
            user_api -> db "POST/send_a_message/{login=<>,password=<>,target=<>,body=<>}"

            frontend -> user_api "Получение списка сообщения для пользователя"        
            user_api -> db "GET/get_chat/login=<>,target=<>"

        }

        themes default 
        systemContext socialNetwork "ContextDiagram" {
            include *
            autoLayout lr
        }
        container socialNetwork {
            include *
            autoLayout lr
        }
    }
}
