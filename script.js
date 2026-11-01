
document.addEventListener('DOMContentLoaded', function() {

    // Анимация галереи
    const galleryItems = document.querySelectorAll('.gallery-item');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15
    });

    galleryItems.forEach((item) => {
        observer.observe(item);
    });

    // Отправка заявки
    const contactForm = document.querySelector('.contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const button = contactForm.querySelector('button');
            button.disabled = true;
            button.textContent = 'ОТПРАВКА...';

            const inputs = contactForm.querySelectorAll('input');
            const textarea = contactForm.querySelector('textarea');

            const application = {
                name: inputs[0].value,
                phone: inputs[1].value,
                email: inputs[2].value,
                message: textarea.value
            };

            try {
                const response = await fetch('/api/applications', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(application)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.message || 'Ошибка отправки');
                }

                alert('Спасибо! Ваша заявка успешно отправлена.');
                contactForm.reset();

            } catch (error) {
                alert('Не удалось отправить заявку. ' + error.message);
            } finally {
                button.disabled = false;
                button.textContent = 'ОТПРАВИТЬ ЗАЯВКУ';
            }
        });
    }
});
