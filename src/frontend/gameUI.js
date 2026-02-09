/**
 * gameUI.js - Game UI Manager for Jump Jump
 * Handles DOM manipulation and UI updates
 */

class GameUI {
    constructor() {
        this.elements = {};
        this.typingSpeed = 30; // ms per character
        this.isTyping = false;
        this.init();
    }

    init() {
        // Cache DOM elements
        this.elements = {
            narrativeDisplay: document.getElementById('narrative-display'),
            sceneIndicator: document.getElementById('scene-indicator'),
            turnIndicator: document.getElementById('turn-indicator'),
            behindScenes: document.getElementById('behind-scenes'),
            behindScenesContent: document.getElementById('behind-scenes-content'),
            decisionPanel: document.getElementById('decision-panel'),
            decisionTitle: document.getElementById('decision-title'),
            decisionDescription: document.getElementById('decision-description'),
            decisionChoices: document.getElementById('decision-choices'),
            actionButtons: document.getElementById('action-buttons'),
            insightTruePurpose: document.getElementById('insight-true-purpose'),
            insightBehindDialogue: document.getElementById('insight-behind-dialogue'),
            btnInsight: document.getElementById('btn-insight'),
            variablesDisplay: document.getElementById('variables-display'),
            connectionStatus: document.getElementById('connection-status'),
            insightModal: document.getElementById('insight-modal'),
            insightOptions: document.getElementById('insight-options'),
            insightResult: document.getElementById('insight-result'),
            transitionModal: document.getElementById('transition-modal'),
            transitionText: document.getElementById('transition-text'),
            btnContinue: document.getElementById('btn-continue'),
        };

        // Bind event listeners
        this.bindEvents();
    }

    bindEvents() {
        // Insight button
        if (this.elements.btnInsight) {
            this.elements.btnInsight.addEventListener('click', () => this.showInsightModal());
        }

        // Modal close buttons
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });

        // Continue button for scene transition
        if (this.elements.btnContinue) {
            this.elements.btnContinue.addEventListener('click', () => {
                this.hideTransitionModal();
            });
        }

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target);
            }
        });
    }

    // Narrative Display
    async displayNarrative(text, emotionBeat = '', typingEffect = true) {
        const display = this.elements.narrativeDisplay;

        // Create new paragraph
        const p = document.createElement('p');
        p.className = 'narrative-text';
        display.appendChild(p);

        if (typingEffect) {
            this.isTyping = true;
            p.classList.add('typing');

            for (let i = 0; i < text.length; i++) {
                p.textContent += text[i];
                await this.sleep(this.typingSpeed);
            }

            p.classList.remove('typing');
            this.isTyping = false;
        } else {
            p.textContent = text;
        }

        // Add emotion beat if provided
        if (emotionBeat) {
            const emotion = document.createElement('span');
            emotion.className = 'emotion-beat';
            emotion.textContent = ` [${emotionBeat}]`;
            emotion.style.color = 'var(--accent-gold)';
            emotion.style.fontSize = '0.9rem';
            p.appendChild(emotion);
        }

        // Scroll to bottom
        display.scrollTop = display.scrollHeight;
    }

    clearNarrative() {
        this.elements.narrativeDisplay.innerHTML = '';
    }

    // Behind-the-Scenes Panel
    showBehindScenes(reveals) {
        const panel = this.elements.behindScenes;
        const content = this.elements.behindScenesContent;

        content.innerHTML = '';

        reveals.forEach(reveal => {
            const div = document.createElement('div');
            div.className = 'reveal-item';
            div.textContent = reveal.content || reveal;
            content.appendChild(div);
        });

        panel.classList.remove('hidden');
    }

    hideBehindScenes() {
        this.elements.behindScenes.classList.add('hidden');
    }

    // Decision Panel
    showDecision(decisionId, title, description, choices, onSelect) {
        const panel = this.elements.decisionPanel;
        const choicesContainer = this.elements.decisionChoices;

        this.elements.decisionTitle.textContent = title || '决策';
        this.elements.decisionDescription.textContent = description || '';

        choicesContainer.innerHTML = '';

        choices.forEach(choice => {
            const btn = document.createElement('button');
            btn.className = 'choice-btn';
            btn.innerHTML = `
                <span class="choice-text">${choice.text || choice.label || '选择'}</span>
                ${choice.preview_hint ? `<span class="hint">${choice.preview_hint}</span>` : ''}
            `;
            btn.addEventListener('click', () => {
                onSelect(decisionId, choice.id);
                this.hideDecision();
            });
            choicesContainer.appendChild(btn);
        });

        panel.classList.remove('hidden');
    }

    hideDecision() {
        this.elements.decisionPanel.classList.add('hidden');
    }

    // Action Buttons
    showActionButtons(actions, onAction) {
        const container = this.elements.actionButtons;
        container.innerHTML = '';

        actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.textContent = action.description || action.type;
            btn.addEventListener('click', () => onAction(action));
            container.appendChild(btn);
        });
    }

    clearActionButtons() {
        this.elements.actionButtons.innerHTML = '';
    }

    // Insight System
    updateInsightQuota(truePurpose, behindDialogue) {
        const tpElement = this.elements.insightTruePurpose;
        const bdElement = this.elements.insightBehindDialogue;

        tpElement.textContent = truePurpose;
        bdElement.textContent = behindDialogue;

        // Update visual state
        tpElement.classList.toggle('empty', truePurpose === 0);
        bdElement.classList.toggle('empty', behindDialogue === 0);

        // Enable/disable insight button
        const hasInsights = truePurpose > 0 || behindDialogue > 0;
        this.elements.btnInsight.disabled = !hasInsights;
    }

    showInsightModal() {
        const modal = this.elements.insightModal;
        const options = this.elements.insightOptions;

        options.innerHTML = '';

        // Get current quota
        const tpCount = parseInt(this.elements.insightTruePurpose.textContent);
        const bdCount = parseInt(this.elements.insightBehindDialogue.textContent);

        // True Purpose option
        const tpOption = document.createElement('div');
        tpOption.className = `insight-option ${tpCount === 0 ? 'disabled' : ''}`;
        tpOption.innerHTML = `
            <h4>真实目的 (${tpCount} 剩余)</h4>
            <p>揭示NPC此刻的真实目的和隐藏动机</p>
        `;
        if (tpCount > 0) {
            tpOption.addEventListener('click', () => this.onInsightSelect('true_purpose'));
        }
        options.appendChild(tpOption);

        // Behind Dialogue option
        const bdOption = document.createElement('div');
        bdOption.className = `insight-option ${bdCount === 0 ? 'disabled' : ''}`;
        bdOption.innerHTML = `
            <h4>幕后对话 (${bdCount} 剩余)</h4>
            <p>揭示隐藏对话层和幕后信息</p>
        `;
        if (bdCount > 0) {
            bdOption.addEventListener('click', () => this.onInsightSelect('behind_dialogue'));
        }
        options.appendChild(bdOption);

        this.elements.insightResult.classList.add('hidden');
        modal.classList.remove('hidden');
    }

    hideInsightModal() {
        this.elements.insightModal.classList.add('hidden');
    }

    showInsightResult(result) {
        const resultDiv = this.elements.insightResult;
        resultDiv.innerHTML = '';

        const title = document.createElement('h4');
        title.textContent = result.type === 'true_purpose' ? '真实目的揭示' : '幕后对话揭示';
        resultDiv.appendChild(title);

        const content = document.createElement('p');
        if (result.type === 'true_purpose') {
            content.innerHTML = `
                <strong>${result.npc_name || result.npc_id}</strong><br>
                真实意图: ${result.true_intent}<br>
                ${result.true_emotional_state ? `真实情绪: ${result.true_emotional_state}<br>` : ''}
                ${result.reasoning ? `推理: ${result.reasoning.join(', ')}` : ''}
            `;
        } else {
            content.innerHTML = `
                <strong>幕后对话链</strong><br>
                共 ${result.chain_length} 层交互<br>
                ${result.summary || ''}
            `;
        }
        resultDiv.appendChild(content);

        resultDiv.classList.remove('hidden');
    }

    setInsightCallback(callback) {
        this.onInsightSelect = callback;
    }

    // Variables Display
    updateVariables(variables) {
        const container = this.elements.variablesDisplay;
        container.innerHTML = '';

        const varTranslations = {
            'faith_erosion_level': '信念侵蚀',
            'nezha_trust': '哪吒信任度',
            'lijing_hesitation': '李靖犹豫度',
            'juanlian_suspicion': '卷帘怀疑度',
            'peach_tree_fate': '桃树命运',
            'sutra_truth': '经文真相',
        };

        Object.entries(variables).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                const item = document.createElement('div');
                item.className = 'variable-item';
                item.innerHTML = `
                    <span class="var-name">${varTranslations[key] || key}</span>
                    <span class="var-value">${value}</span>
                `;
                container.appendChild(item);
            }
        });
    }

    // Connection Status
    setConnectionStatus(status) {
        const indicator = this.elements.connectionStatus;
        indicator.className = 'connection-status ' + status;

        const messages = {
            connected: '已连接',
            disconnected: '未连接',
            connecting: '连接中...'
        };
        indicator.textContent = messages[status] || status;
    }

    // Scene Transition
    showTransitionModal(fromScene, toScene, text) {
        const modal = this.elements.transitionModal;
        const textElement = this.elements.transitionText;

        textElement.textContent = text || `从 ${fromScene} 前往 ${toScene}...`;
        modal.classList.remove('hidden');
    }

    hideTransitionModal() {
        this.elements.transitionModal.classList.add('hidden');
    }

    // Game Meta
    updateSceneIndicator(scene) {
        const sceneNames = {
            'scene-0-wuzhishan': '五指山',
            'scene-1-chentangguan': '陈塘关',
            'scene-2-tianhe': '天河',
            'scene-3-huaguoshan': '花果山',
            'scene-4-lingtai': '灵台方寸山'
        };
        this.elements.sceneIndicator.textContent = `场景: ${sceneNames[scene] || scene}`;
    }

    updateTurnIndicator(turn) {
        this.elements.turnIndicator.textContent = `回合: ${turn}`;
    }

    // Modal Utilities
    closeModal(modal) {
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Utility
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in app.js
window.GameUI = GameUI;
