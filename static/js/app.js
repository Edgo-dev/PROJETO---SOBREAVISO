(function () {
    "use strict";

    // ====================================================================
    // Sidebar toggle (hambúrguer): oculta/exibe o menu lateral com transição
    // suave. Estado persistido em localStorage. No mobile vira overlay.
    // ====================================================================
    (function setupSidebarToggle() {
        var layout = document.getElementById("app-layout");
        var toggle = document.querySelector("[data-sidebar-toggle]");
        var backdrop = document.querySelector("[data-sidebar-backdrop]");
        if (!layout || !toggle) {
            return;
        }

        var STORAGE_KEY = "sobreaviso:sidebar-collapsed";
        var MOBILE_QUERY = "(max-width: 768px)";

        function isMobile() {
            return window.matchMedia && window.matchMedia(MOBILE_QUERY).matches;
        }

        function readPreference() {
            try {
                return window.localStorage.getItem(STORAGE_KEY) === "1";
            } catch (e) {
                return false;
            }
        }

        function writePreference(collapsed) {
            try {
                window.localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
            } catch (e) {
                // sem storage disponivel; segue sem persistir
            }
        }

        function applyState(collapsed, opts) {
            opts = opts || {};
            if (isMobile()) {
                // No mobile, o sidebar começa fechado; classe is-open controla abertura.
                if (collapsed) {
                    layout.classList.remove("is-open");
                } else {
                    layout.classList.add("is-open");
                }
                layout.classList.add("is-collapsed");
            } else {
                if (collapsed) {
                    layout.classList.add("is-collapsed");
                } else {
                    layout.classList.remove("is-collapsed");
                }
                layout.classList.remove("is-open");
            }
            toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
            if (opts.persist !== false) {
                writePreference(collapsed);
            }
        }

        // Estado inicial: no mobile sempre começa fechado; no desktop lê preferência.
        var initialCollapsed = isMobile() ? true : readPreference();
        applyState(initialCollapsed, { persist: false });

        toggle.addEventListener("click", function () {
            var isCollapsedNow;
            if (isMobile()) {
                isCollapsedNow = !layout.classList.contains("is-open");
            } else {
                isCollapsedNow = layout.classList.contains("is-collapsed");
            }
            applyState(!isCollapsedNow);
        });

        if (backdrop) {
            backdrop.addEventListener("click", function () {
                if (isMobile()) {
                    applyState(true);
                }
            });
        }

        // Atualiza ao redimensionar entre mobile/desktop.
        if (window.matchMedia) {
            var mq = window.matchMedia(MOBILE_QUERY);
            var onChange = function () {
                applyState(readPreference(), { persist: false });
            };
            if (typeof mq.addEventListener === "function") {
                mq.addEventListener("change", onChange);
            } else if (typeof mq.addListener === "function") {
                mq.addListener(onChange);
            }
        }
    })();

    function copiarTexto(texto) {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(texto);
        }

        var textarea = document.createElement("textarea");
        textarea.value = texto;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        return Promise.resolve();
    }

    document.querySelectorAll("[data-copy-target]").forEach(function (button) {
        button.addEventListener("click", function () {
            var targetId = button.getAttribute("data-copy-target");
            var target = document.getElementById(targetId);

            if (!target) {
                return;
            }

            var originalText = button.textContent;
            copiarTexto(target.textContent).then(function () {
                button.textContent = "Copiado!";
                window.setTimeout(function () {
                    button.textContent = originalText;
                }, 2500);
            });
        });
    });

    // Filtros dinamicos: envia o form automaticamente conforme o usuario digita.
    // Selects disparam imediatamente; campos de texto usam debounce de 350ms.
    document.querySelectorAll("form[data-auto-submit]").forEach(function (form) {
        var timer = null;

        function submitForm() {
            // Reset pagina ao mudar filtros para nao "preservar" pagina invalida.
            var paginaInput = form.querySelector('input[name="page"]');
            if (paginaInput) {
                paginaInput.value = "";
            }
            form.submit();
        }

        var inputs = form.querySelectorAll("[data-auto-submit-input]");
        inputs.forEach(function (input) {
            var ehTextual = input.tagName === "INPUT" && input.type !== "checkbox";
            if (ehTextual) {
                input.addEventListener("input", function () {
                    window.clearTimeout(timer);
                    timer = window.setTimeout(submitForm, 350);
                });
            } else {
                input.addEventListener("change", submitForm);
            }
        });
    });

    // Combobox de busca de ativos: input textual com sugestoes do backend.
    // Dispara 'change' no hidden input #id_ativo para acionar o painel de obras.
    document.querySelectorAll("[data-combobox]").forEach(function (root) {
        var endpoint = root.getAttribute("data-combobox-endpoint");
        var input = root.querySelector("[data-combobox-input]");
        var list = root.querySelector("[data-combobox-list]");
        var clearBtn = root.querySelector("[data-combobox-clear]");
        var hidden = root.querySelector("input[type='hidden']");
        if (!endpoint || !input || !list || !hidden) {
            return;
        }

        var timer = null;
        var activeIndex = -1;
        var currentItems = [];
        var currentTerm = "";
        var currentOffset = 0;
        var hasMore = false;
        var carregando = false;

        function escapeHtml(texto) {
            if (texto === null || texto === undefined) {
                return "";
            }
            return String(texto)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function abrirLista() {
            list.hidden = false;
            input.setAttribute("aria-expanded", "true");
        }

        function fecharLista() {
            list.hidden = true;
            input.setAttribute("aria-expanded", "false");
            activeIndex = -1;
        }

        function atualizarClearBtn() {
            if (!clearBtn) return;
            clearBtn.hidden = !(hidden.value || input.value);
        }

        function dispararChange() {
            var ev;
            try {
                ev = new Event("change", { bubbles: true });
            } catch (e) {
                ev = document.createEvent("Event");
                ev.initEvent("change", true, true);
            }
            hidden.dispatchEvent(ev);
        }

        function selecionarItem(item) {
            hidden.value = item.id;
            input.value = item.label || "";
            atualizarClearBtn();
            fecharLista();
            dispararChange();
        }

        function destacarItem(novoIndice) {
            var nodes = list.querySelectorAll("[data-combobox-item]");
            nodes.forEach(function (node, i) {
                if (i === novoIndice) {
                    node.classList.add("is-active");
                    node.setAttribute("aria-selected", "true");
                } else {
                    node.classList.remove("is-active");
                    node.removeAttribute("aria-selected");
                }
            });
            activeIndex = novoIndice;
        }

        function renderEmpty(mensagem) {
            currentItems = [];
            list.innerHTML = '<li class="combobox-empty">' + escapeHtml(mensagem) + '</li>';
            abrirLista();
        }

        function itemHtml(item, i) {
            return ''
                + '<li class="combobox-item" role="option" data-combobox-item data-index="' + i + '">'
                +   '<span class="combobox-item-label">' + escapeHtml(item.label) + '</span>'
                +   (item.sub ? '<span class="combobox-item-sub">' + escapeHtml(item.sub) + '</span>' : '')
                + '</li>';
        }

        function renderInicial(resultados, total) {
            currentItems = resultados.slice();
            if (!resultados || resultados.length === 0) {
                renderEmpty("Nenhum ativo encontrado");
                return;
            }
            var html = resultados.map(itemHtml).join("");
            if (total > resultados.length) {
                html += '<li class="combobox-total">Mostrando ' + resultados.length + ' de ' + total + ' ativos — role para ver mais</li>';
            }
            list.innerHTML = html;
            abrirLista();
            destacarItem(-1);
            list.scrollTop = 0;
        }

        function anexarMais(resultados) {
            if (!resultados || resultados.length === 0) {
                return;
            }
            var baseIndex = currentItems.length;
            var html = resultados.map(function (item, i) {
                return itemHtml(item, baseIndex + i);
            }).join("");
            // Remove footer "Mostrando X de Y" antes de anexar, será re-adicionado se faltar.
            var footer = list.querySelector(".combobox-total");
            if (footer) footer.remove();
            list.insertAdjacentHTML("beforeend", html);
            for (var i = 0; i < resultados.length; i++) {
                currentItems.push(resultados[i]);
            }
        }

        function atualizarRodape(total) {
            var footer = list.querySelector(".combobox-total");
            if (footer) footer.remove();
            if (total > currentItems.length) {
                var li = document.createElement("li");
                li.className = "combobox-total";
                li.textContent = "Mostrando " + currentItems.length + " de " + total + " ativos — role para ver mais";
                list.appendChild(li);
            }
        }

        function buscar(termo, opts) {
            opts = opts || {};
            var append = !!opts.append;
            if (carregando) return;
            carregando = true;

            if (!append) {
                currentTerm = termo || "";
                currentOffset = 0;
            }

            var url = endpoint
                + "?q=" + encodeURIComponent(currentTerm)
                + "&offset=" + encodeURIComponent(currentOffset);

            fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
                .then(function (resp) {
                    if (!resp.ok) { throw new Error("HTTP " + resp.status); }
                    return resp.json();
                })
                .then(function (data) {
                    var resultados = data.results || [];
                    hasMore = !!data.has_more;
                    if (append) {
                        anexarMais(resultados);
                        currentOffset += resultados.length;
                        atualizarRodape(data.total || currentItems.length);
                    } else {
                        renderInicial(resultados, data.total || resultados.length);
                        currentOffset = resultados.length;
                    }
                })
                .catch(function () {
                    if (!append) {
                        renderEmpty("Não foi possível buscar agora");
                    }
                })
                .finally(function () {
                    carregando = false;
                });
        }

        input.addEventListener("input", function () {
            // Ao digitar, invalida a selecao atual ate o usuario escolher de novo.
            if (hidden.value) {
                hidden.value = "";
                dispararChange();
            }
            atualizarClearBtn();
            window.clearTimeout(timer);
            var termo = input.value.trim();
            timer = window.setTimeout(function () { buscar(termo); }, 200);
        });

        input.addEventListener("focus", function () {
            if (input.value.trim() || !hidden.value) {
                buscar(input.value.trim());
            }
        });

        input.addEventListener("keydown", function (ev) {
            if (list.hidden) {
                if (ev.key === "ArrowDown") {
                    buscar(input.value.trim());
                    ev.preventDefault();
                }
                return;
            }
            if (ev.key === "ArrowDown") {
                ev.preventDefault();
                if (currentItems.length === 0) return;
                destacarItem((activeIndex + 1) % currentItems.length);
            } else if (ev.key === "ArrowUp") {
                ev.preventDefault();
                if (currentItems.length === 0) return;
                destacarItem(activeIndex <= 0 ? currentItems.length - 1 : activeIndex - 1);
            } else if (ev.key === "Enter") {
                if (activeIndex >= 0 && currentItems[activeIndex]) {
                    ev.preventDefault();
                    selecionarItem(currentItems[activeIndex]);
                }
            } else if (ev.key === "Escape") {
                fecharLista();
            }
        });

        list.addEventListener("mousedown", function (ev) {
            // mousedown (nao click) para evitar perder o focus antes do handler rodar.
            var li = ev.target.closest("[data-combobox-item]");
            if (!li) return;
            ev.preventDefault();
            var i = parseInt(li.getAttribute("data-index"), 10);
            if (!isNaN(i) && currentItems[i]) {
                selecionarItem(currentItems[i]);
            }
        });

        // Scroll infinito: ao chegar perto do fim, busca o proximo lote.
        list.addEventListener("scroll", function () {
            if (carregando || !hasMore) return;
            var restante = list.scrollHeight - list.scrollTop - list.clientHeight;
            if (restante < 60) {
                buscar(currentTerm, { append: true });
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                input.value = "";
                hidden.value = "";
                atualizarClearBtn();
                fecharLista();
                input.focus();
                dispararChange();
            });
        }

        document.addEventListener("click", function (ev) {
            if (!root.contains(ev.target)) {
                fecharLista();
            }
        });

        atualizarClearBtn();
    });

    // Painel lateral de status de obra + auto-preenchimento dos campos do ativo
    // no formulario de Novo Chamado.
    // Estados do painel: is-empty (sem ativo) | is-clean (ativo OK, sem obras) | is-warning (obras detectadas).
    var obraPanel = document.getElementById("obra-side-panel");
    var ativoSelect = document.getElementById("id_ativo");
    if (obraPanel && ativoSelect) {
        var endpointTemplate = obraPanel.getAttribute("data-obras-endpoint") || "";
        var listaEl = document.getElementById("obra-side-list");
        var statusTextEl = obraPanel.querySelector("[data-status-text]");

        // Campos readonly que sao auto-preenchidos a partir do Ativo selecionado.
        var displayMap = {
            "display-nome-site": "nome_site",
            "display-endereco": "endereco",
            "display-cidade": "cidade",
            "display-uf": "uf",
            "display-regional": "regional",
            "display-tipo-imovel": "tipo_imovel",
            "display-tipo-sla": "tipo_site_sla",
            "display-lider": "lider_coordenacao",
        };

        function preencherDisplays(dados) {
            Object.keys(displayMap).forEach(function (elId) {
                var el = document.getElementById(elId);
                if (!el) return;
                var chave = displayMap[elId];
                el.value = (dados && dados[chave]) ? dados[chave] : "";
            });
        }

        function limparDisplays() {
            preencherDisplays(null);
        }

        function escapeHtml(texto) {
            if (texto === null || texto === undefined) {
                return "";
            }
            return String(texto)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function setEstado(estado, statusText) {
            obraPanel.classList.remove("is-empty", "is-clean", "is-warning");
            obraPanel.classList.add("is-" + estado);
            if (statusTextEl && statusText) {
                statusTextEl.textContent = statusText;
            }
        }

        function renderObras(obras) {
            if (!listaEl) {
                return;
            }
            listaEl.innerHTML = obras.map(function (obra) {
                var responsavel = obra.responsavel && obra.responsavel.trim()
                    ? escapeHtml(obra.responsavel)
                    : "&mdash;";
                return ''
                    + '<li class="obra-side-item">'
                    +   '<header class="obra-side-item-head">'
                    +     '<span class="status-pill situacao-' + escapeHtml(obra.situacao) + '">'
                    +       '<span class="status-dot"></span> ' + escapeHtml(obra.situacao_label)
                    +     '</span>'
                    +     '<a href="' + escapeHtml(obra.detalhe_url) + '" class="btn btn-link" target="_blank" rel="noopener">'
                    +       'Detalhe &#8599;'
                    +     '</a>'
                    +   '</header>'
                    +   '<p class="obra-side-descricao">' + escapeHtml(obra.descricao).replace(/\n/g, "<br>") + '</p>'
                    +   '<dl class="obra-side-meta">'
                    +     '<div><dt>Início</dt><dd>' + escapeHtml(obra.data_inicio_br) + '</dd></div>'
                    +     '<div><dt>Fim planejado</dt><dd>' + escapeHtml(obra.data_fim_planejada_br) + '</dd></div>'
                    +     '<div><dt>Responsável</dt><dd>' + responsavel + '</dd></div>'
                    +   '</dl>'
                    + '</li>';
            }).join("");
        }

        function atualizarObras() {
            var pk = ativoSelect.value;
            if (!pk) {
                setEstado("empty", "Aguardando seleção do ativo");
                if (listaEl) { listaEl.innerHTML = ""; }
                limparDisplays();
                return;
            }
            var url = endpointTemplate.replace(/\/0\//, "/" + encodeURIComponent(pk) + "/");
            fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
                .then(function (resp) {
                    if (!resp.ok) { throw new Error("HTTP " + resp.status); }
                    return resp.json();
                })
                .then(function (data) {
                    preencherDisplays(data);
                    if (data.obras && data.obras.length > 0) {
                        renderObras(data.obras);
                        var n = data.obras.length;
                        var texto = n === 1
                            ? "Obra em andamento neste endereço"
                            : n + " obras em andamento neste endereço";
                        setEstado("warning", texto);
                    } else {
                        if (listaEl) { listaEl.innerHTML = ""; }
                        setEstado("clean", "Endereço livre — sem obras em curso");
                    }
                })
                .catch(function () {
                    setEstado("empty", "Não foi possível verificar obras no momento");
                });
        }

        ativoSelect.addEventListener("change", atualizarObras);
        // Se chegou na pagina com ativo selecionado mas sem obras renderizadas server-side,
        // confirma com o backend para nao mostrar "clean" prematuramente e ja preenche displays.
        if (ativoSelect.value && obraPanel.classList.contains("is-clean")) {
            atualizarObras();
        }
    }
})();
