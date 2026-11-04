<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <style>
        :root {
            color-scheme: dark;
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            background: transparent;
            color: #f8fafc;
            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        .field {
            padding: 4px;
        }

        label {
            display: block;
            margin-bottom: 9px;
            color: #ffffff;
            font-size: 14px;
            font-weight: 700;
        }

        .input-wrap {
            display: flex;
            align-items: center;
            min-height: 48px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 12px;
            background: #0b1322;
            transition:
                border-color 150ms ease,
                box-shadow 150ms ease;
        }

        .input-wrap:focus-within {
            border-color: #22d3ee;
            box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.13);
        }

        .icon {
            padding-left: 13px;
            padding-right: 8px;
        }

        input {
            display: block;
            width: 100%;
            min-width: 0;
            height: 46px;
            padding: 0 12px 0 0;
            border: 0;
            outline: none;
            background: transparent;
            color: #f8fafc;
            font: inherit;
            font-size: 16px;
        }

        input::placeholder {
            color: #8b9bb3;
            opacity: 1;
        }
    </style>
</head>

<body>
    <div class="field">
        <label for="destination">Куда отправляемся?</label>

        <div class="input-wrap">
            <span class="icon" aria-hidden="true">📍</span>

            <input
                id="destination"
                type="text"
                autocomplete="off"
                spellcheck="false"
                maxlength="300"
                placeholder="Город, регион, посёлок или страна"
            >
        </div>
    </div>

    <script>
        const input = document.getElementById("destination");

        let initialized = false;
        let timer = null;
        let lastSentValue = "";
        let sequence = 0;

        // Уникальный идентификатор экземпляра фронтенда.
        const instanceId =
            Date.now().toString(36) +
            "-" +
            Math.random().toString(36).slice(2);

        function sendMessage(type, payload = {}) {
            window.parent.postMessage(
                {
                    isStreamlitMessage: true,
                    type: type,
                    ...payload
                },
                "*"
            );
        }

        function updateHeight() {
            const height = Math.ceil(
                document.querySelector(".field")
                    .getBoundingClientRect().height
            ) + 8;

            sendMessage("streamlit:setFrameHeight", {height});
        }

        function sendInput() {
            clearTimeout(timer);

            if (!initialized || input.value === lastSentValue) {
                return;
            }

            lastSentValue = input.value;
            sequence += 1;

            sendMessage("streamlit:setComponentValue", {
                dataType: "
