document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-menu-toggle]').forEach((botao) => {
        const seletor = botao.getAttribute('data-menu-toggle');
        const menu = document.querySelector(seletor);

        if (!menu) {
            return;
        }

        botao.addEventListener('click', () => {
            const aberto = menu.classList.toggle('ativo');
            botao.setAttribute('aria-expanded', aberto ? 'true' : 'false');
        });
    });
});
