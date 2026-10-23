
import { useState } from "react";
import "./App.css";

const translations = {
  ru: {
    menu: ["Главная", "Возможности", "Как это работает"],
    login: "Войти",
    register: "Создать аккаунт",
    eyebrow: "NOMAD COLLEGE · ONLINE RECORD",
    title: "Твое образование.",
    titleAccent: "Твой следующий шаг.",
    description:
      "Записывайся на консультации, выбирай удобное время и следи за своими обращениями в одном месте.",
    start: "Начать сейчас",
    learn: "Как это работает",
    available: "ОНЛАЙН-СЕРВИС КОЛЛЕДЖА",
    panelTitle: "Всё начинается здесь.",
    panelText: "Выбери нужную услугу и запланируй визит без лишней суеты.",
    feature1: "Удобная запись",
    feature2: "Контроль обращений",
    feature3: "Расписание онлайн",
    sectionLabel: "ПРОСТО. УДОБНО. В ОДНОМ МЕСТЕ.",
    sectionTitle: "Меньше ожидания. Больше возможностей.",
    sectionText:
      "Все основные действия доступны онлайн — когда тебе удобно.",
    stepsTitle: "Три шага — и готово.",
    steps: [
      ["01", "Создай аккаунт", "Зарегистрируйся, чтобы пользоваться личным кабинетом."],
      ["02", "Выбери время", "Посмотри доступные варианты и выбери удобный."],
      ["03", "Следи за записью", "Проверяй детали своего обращения в личном кабинете."],
    ],
    ctaTitle: "Готов начать?",
    ctaText: "Перейди к онлайн-сервису Nomad College.",
    footer: "Сервис онлайн-записи",
    copyright: "NOMAD COLLEGE. Все права защищены.",
    loginTitle: "С возвращением",
    registerTitle: "Создать аккаунт",
    username: "Имя пользователя",
    password: "Пароль",
    close: "Закрыть",
    demoNote:
      "Форма пока демонстрационная. Подключение к серверу будет следующим этапом.",
  },
  kg: {
    menu: ["Башкы бет", "Мүмкүнчүлүктөр", "Кантип иштейт"],
    login: "Кирүү",
    register: "Аккаунт түзүү",
    eyebrow: "NOMAD COLLEGE · ONLINE RECORD",
    title: "Сенин билимиң.",
    titleAccent: "Сенин кийинки кадамың.",
    description:
      "Кеңеш алууга жазыл, ыңгайлуу убакытты танда жана кайрылууларыңды бир жерден көзөмөлдө.",
    start: "Азыр баштоо",
    learn: "Кантип иштейт",
    available: "КОЛЛЕДЖДИН ОНЛАЙН КЫЗМАТЫ",
    panelTitle: "Баары ушул жерден башталат.",
    panelText: "Керектүү кызматты тандап, убакытты алдын ала планда.",
    feature1: "Ыңгайлуу жазылуу",
    feature2: "Кайрылууларды көзөмөлдөө",
    feature3: "Онлайн график",
    sectionLabel: "ЖӨНӨКӨЙ. ЫҢГАЙЛУУ. БИР ЖЕРДЕ.",
    sectionTitle: "Аз күтүү. Көбүрөөк мүмкүнчүлүк.",
    sectionText: "Негизги кызматтар онлайн жеткиликтүү.",
    stepsTitle: "Үч кадам — даяр.",
    steps: [
      ["01", "Аккаунт түз", "Жеке кабинетти колдонуу үчүн каттал."],
      ["02", "Убакытты танда", "Жеткиликтүү убакыттардын бирин танда."],
      ["03", "Жазылууну көзөмөлдө", "Кайрылууңдун маалыматын жеке кабинеттен текшер."],
    ],
    ctaTitle: "Баштоого даярсыңбы?",
    ctaText: "Nomad College онлайн кызматына өт.",
    footer: "Онлайн жазылуу кызматы",
    copyright: "NOMAD COLLEGE. Бардык укуктар корголгон.",
    loginTitle: "Кайра кош келиңиз",
    registerTitle: "Аккаунт түзүү",
    username: "Колдонуучунун аты",
    password: "Сырсөз",
    close: "Жабуу",
    demoNote: "Форма азырынча көрсөтмө үчүн. Серверге туташтыруу кийинки этапта болот.",
  },
  en: {
    menu: ["Home", "Features", "How it works"],
    login: "Log in",
    register: "Create account",
    eyebrow: "NOMAD COLLEGE · ONLINE RECORD",
    title: "Your education.",
    titleAccent: "Your next step.",
    description:
      "Book consultations, choose a convenient time, and keep track of your requests in one place.",
    start: "Get started",
    learn: "How it works",
    available: "COLLEGE ONLINE SERVICE",
    panelTitle: "It starts here.",
    panelText: "Choose the service you need and plan your visit with ease.",
    feature1: "Easy booking",
    feature2: "Track requests",
    feature3: "Online schedule",
    sectionLabel: "SIMPLE. CONVENIENT. IN ONE PLACE.",
    sectionTitle: "Less waiting. More possibilities.",
    sectionText: "Access essential services online whenever it suits you.",
    stepsTitle: "Three steps. That's it.",
    steps: [
      ["01", "Create an account", "Register to access your personal account."],
      ["02", "Choose a time", "Review available options and pick a suitable time."],
      ["03", "Track your booking", "Check your request details in your account."],
    ],
    ctaTitle: "Ready to begin?",
    ctaText: "Explore the Nomad College online service.",
    footer: "Online booking service",
    copyright: "NOMAD COLLEGE. All rights reserved.",
    loginTitle: "Welcome back",
    registerTitle: "Create account",
    username: "Username",
    password: "Password",
    close: "Close",
    demoNote: "This form is a preview. Server integration comes next.",
  },
};

function App() {
  const [language, setLanguage] = useState("ru");
  const [modal, setModal] = useState("");
  const t = translations[language];

  function openModal(type) {
    setModal(type);
  }

  return (
    <div className="app">
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="#home" aria-label="Nomad College">
            <img
              className="brand-logo"
              src="/logo.png.webp"
              alt="Nomad College"
            />
            <span className="brand-name">
              <strong>NOMAD</strong>
              <small>COLLEGE · ONLINE RECORD</small>
            </span>
          </a>

          <nav className="main-nav">
            <a href="#home">{t.menu[0]}</a>
            <a href="#features">{t.menu[1]}</a>
            <a href="#steps">{t.menu[2]}</a>
          </nav>

          <div className="header-actions">
            <select
              className="language-select"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              aria-label="Language"
            >
              <option value="ru">RU</option>
              <option value="kg">KG</option>
              <option value="en">EN</option>
            </select>
            <button
              className="button button-login"
              onClick={() => openModal("login")}
            >
              {t.login}
            </button>
            <button
              className="button button-red header-register"
              onClick={() => openModal("register")}
            >
              {t.register}
              <span aria-hidden="true">↗</span>
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-inner">
            <div className="hero-copy">
              <div className="eyebrow">
                <span className="eyebrow-dot" />
                {t.eyebrow}
              </div>

              <h1>
                {t.title}
                <br />
                <span>{t.titleAccent}</span>
              </h1>

              <p className="hero-description">{t.description}</p>

              <div className="hero-actions">
                <button
                  className="button button-red button-large"
                  onClick={() => openModal("register")}
                >
                  {t.start}
                  <span aria-hidden="true">↗</span>
                </button>
                <a className="button button-outline button-large" href="#steps">
                  {t.learn}
                  <span aria-hidden="true">↓</span>
                </a>
              </div>

              <div className="hero-note">
                <span className="note-check">✓</span>
                <span>{t.available}</span>
              </div>
            </div>

            <div className="hero-visual">
              <div className="visual-red-shape" />
              <div className="visual-card">
                <div className="visual-card-top">
                  <span className="visual-tag">NOMAD / OR</span>
                  <span className="visual-status">
                    <span />
                    ONLINE
                  </span>
                </div>

                <div className="visual-mark">N.</div>

                <div className="visual-card-content">
                  <div className="visual-small-title">{t.available}</div>
                  <h2>{t.panelTitle}</h2>
                  <p>{t.panelText}</p>
                </div>

                <div className="visual-features">
                  <div className="visual-feature">
                    <span className="feature-icon">01</span>
                    <span>{t.feature1}</span>
                    <span className="feature-arrow">↗</span>
                  </div>
                  <div className="visual-feature">
                    <span className="feature-icon">02</span>
                    <span>{t.feature2}</span>
                    <span className="feature-arrow">↗</span>
                  </div>
                  <div className="visual-feature">
                    <span className="feature-icon">03</span>
                    <span>{t.feature3}</span>
                    <span className="feature-arrow">↗</span>
                  </div>
                </div>

                <div className="visual-card-footer">
                  <span>YOUR FUTURE STARTS HERE</span>
                  <span>2026 — ∞</span>
                </div>
              </div>
              <div className="visual-side-label">LEARN · PLAN · GROW</div>
            </div>
          </div>

          <div className="hero-bottom-line">
            <span>01 / ONLINE SERVICE</span>
            <span>NOMAD COLLEGE — BISHKEK</span>
            <a href="#features">SCROLL TO EXPLORE ↓</a>
          </div>
        </section>

        <section className="features-section" id="features">
          <div className="section-heading">
            <div>
              <div className="section-label">{t.sectionLabel}</div>
              <h2>{t.sectionTitle}</h2>
            </div>
            <p>{t.sectionText}</p>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-card-top">
                <span>01 / BOOKING</span>
                <span className="feature-card-icon">↗</span>
              </div>
              <div className="feature-card-symbol">↗</div>
              <h3>{t.feature1}</h3>
              <p>{t.steps[1][2]}</p>
            </article>

            <article className="feature-card feature-card-dark">
              <div className="feature-card-top">
                <span>02 / CONTROL</span>
                <span className="feature-card-icon">↗</span>
              </div>
              <div className="feature-card-symbol">◎</div>
              <h3>{t.feature2}</h3>
              <p>{t.steps[2][2]}</p>
            </article>

            <article className="feature-card feature-card-red">
              <div className="feature-card-top">
                <span>03 / SCHEDULE</span>
                <span className="feature-card-icon">↗</span>
              </div>
              <div className="feature-card-symbol">◷</div>
              <h3>{t.feature3}</h3>
              <p>{t.panelText}</p>
            </article>
          </div>
        </section>

        <section className="steps-section" id="steps">
          <div className="steps-intro">
            <div className="section-label">HOW IT WORKS / 03 STEPS</div>
            <h2>{t.stepsTitle}</h2>
          </div>

          <div className="steps-list">
            {t.steps.map((step) => (
              <article className="step-row" key={step[0]}>
                <span className="step-index">{step[0]}</span>
                <h3>{step[1]}</h3>
                <p>{step[2]}</p>
                <span className="step-arrow">↗</span>
              </article>
            ))}
          </div>
        </section>

        <section className="cta-section">
          <div className="cta-index">NOMAD COLLEGE / ONLINE RECORD</div>
          <h2>{t.ctaTitle}</h2>
          <p>{t.ctaText}</p>
          <button
            className="button button-light button-large"
            onClick={() => openModal("register")}
          >
            {t.start}
            <span aria-hidden="true">↗</span>
          </button>
          <div className="cta-decoration" aria-hidden="true">
            N
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <a className="footer-brand" href="#home">
          <span className="footer-brand-mark">N.</span>
          <span>
            <strong>NOMAD COLLEGE</strong>
            <small>{t.footer}</small>
          </span>
        </a>
        <p>{t.copyright}</p>
        <a className="back-to-top" href="#home">
          BACK TO TOP ↑
        </a>
      </footer>

      {modal && (
        <div
          className="modal-backdrop"
          onClick={(event) => {
            if (event.target === event.currentTarget) setModal("");
          }}
        >
          <div
            className="auth-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            <button
              className="modal-close"
              onClick={() => setModal("")}
              aria-label={t.close}
            >
              ×
            </button>
            <div className="modal-logo">N.</div>
            <div className="section-label">NOMAD COLLEGE / ONLINE RECORD</div>
            <h2 id="modal-title">
              {modal === "login" ? t.loginTitle : t.registerTitle}
            </h2>
            <p className="modal-note">{t.demoNote}</p>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                window.alert(t.demoNote);
              }}
            >
              <label htmlFor="username">{t.username}</label>
              <input id="username" name="username" autoComplete="username" required />
              <label htmlFor="password">{t.password}</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={modal === "login" ? "current-password" : "new-password"}
                minLength={8}
                required
              />
              <button className="button button-red modal-submit" type="submit">
                {modal === "login" ? t.login : t.register}
                <span aria-hidden="true">↗</span>
              </button>
            </form>
            <button
              className="modal-switch"
              onClick={() => setModal(modal === "login" ? "register" : "login")}
            >
              {modal === "login" ? t.register : t.login}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
