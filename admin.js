
document.addEventListener('DOMContentLoaded', function() {

    const container = document.querySelector('#applications');

    async function loadApplications() {
        try {
            const response = await fetch('/api/applications', {
                cache: 'no-store'
            });

            if (!response.ok) {
                throw new Error('Ошибка загрузки заявок');
            }

            const applications = await response.json();

            container.innerHTML = '';

            if (applications.length === 0) {
                container.textContent = 'Пока заявок нет.';
                return;
            }

            applications.forEach(application => {
                const card = document.createElement('div');
                card.className = 'application-card';

                const title = document.createElement('h3');
                title.textContent = `Заявка №${application.id}`;

                const status = document.createElement('p');
                status.className = application.status === 'completed'
                ? 'application-status completed'
                 : 'application-status new';
                status.textContent = application.status === 'completed'
                    ? 'Статус: Обработана'
                    : 'Статус: Новая';

                const name = document.createElement('p');
                name.textContent = `Имя: ${application.name}`;

                const phone = document.createElement('p');
                phone.textContent = `Телефон: ${application.phone}`;

                const email = document.createElement('p');
                email.textContent = `Почта: ${application.email || 'Не указана'}`;

                const message = document.createElement('p');
                message.textContent = `Описание: ${application.message || 'Не указано'}`;

                const date = document.createElement('p');
                date.textContent = `Дата: ${application.created_at}`;

                const completeButton = document.createElement('button');
                completeButton.textContent = application.status === 'completed'
                    ? 'Вернуть в новые'
                    : 'Отметить обработанной';

                completeButton.addEventListener('click', () => {
                    updateStatus(
                        application.id,
                        application.status === 'completed' ? 'new' : 'completed'
                    );
                });

                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'Удалить';

                deleteButton.addEventListener('click', () => {
                    deleteApplication(application.id);
                });

                card.append(
                    title,
                    status,
                    name,
                    phone,
                    email,
                    message,
                    date,
                    completeButton,
                    deleteButton
                );

                container.appendChild(card);
            });

        } catch (error) {
            container.textContent = 'Не удалось загрузить заявки.';
            console.error(error);
        }
    }

    async function updateStatus(id, status) {
        const response = await fetch(`/api/applications/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            loadApplications();
        } else {
            alert('Не удалось изменить статус.');
        }
    }

    async function deleteApplication(id) {
        if (!confirm('Ты действительно хочешь удалить заявку?')) {
            return;
        }

        const response = await fetch(`/api/applications/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadApplications();
        } else {
            alert('Не удалось удалить заявку.');
        }
    }

    // Первая загрузка заявок
loadApplications();

// Автоматическое обновление каждые 10 секунд
setInterval(loadApplications, 10000);

});