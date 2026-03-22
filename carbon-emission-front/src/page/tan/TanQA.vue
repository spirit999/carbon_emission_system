<template>
  <div class="tan-qa-page">
    <el-card class="qa-card">
      <div slot="header" class="qa-header">
        <span>智能问答助手</span>
      </div>

      <div class="qa-input-area">
        <el-input
          type="textarea"
          v-model="question"
          :rows="4"
          placeholder="请在这里输入与学校碳排放、能耗监测、减碳分析等相关的问题…"
        />
        <div class="qa-actions">
          <el-button type="primary" :loading="loading" @click="handleAsk">
            {{ loading ? '正在生成回答…' : '发送问题' }}
          </el-button>
          <el-button @click="handleClear">清空</el-button>
        </div>
      </div>

      <div v-if="loading || answer" class="qa-answer">
        <h3>系统回答</h3>
        <div
          class="qa-answer-content markdown-body"
          v-html="answerHtml"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { askQuestionStream, askQuestion } from '../../api/qa';

export default {
  name: 'TanQA',
  data() {
    return {
      question: '',
      answer: '',
      loading: false
    };
  },
  computed: {
    answerHtml() {
      const raw = this.loading && !this.answer ? '正在生成回答…' : this.answer;
      if (!raw) return '';
      const html = marked.parse(raw, { breaks: true });
      return DOMPurify.sanitize(html);
    }
  },
  methods: {
    async handleAsk() {
      const q = this.question && this.question.trim();
      if (!q) {
        this.$message.warning('请先输入问题');
        return;
      }
      this.loading = true;
      this.answer = '';
      try {
        await askQuestionStream(q, (text) => {
          this.answer += text;
        });
      } catch (e) {
        this.$message.info('流式请求异常，正在改用普通模式重试…');
        try {
          const res = await askQuestion(q);
          this.answer = (res.data && res.data.data) || '暂无回答内容';
        } catch (e2) {
          this.answer = '请求失败，请稍后重试。' + (e2.message || e.message || '');
        }
      } finally {
        this.loading = false;
      }
    },
    handleClear() {
      this.question = '';
      this.answer = '';
    }
  }
};
</script>

<style scoped>
.tan-qa-page {
  padding: 20px;
}

.qa-card {
  max-width: 900px;
  margin: 0 auto;
}

.qa-header {
  font-size: 16px;
  font-weight: 600;
}

.qa-input-area {
  margin-bottom: 20px;
}

.qa-actions {
  margin-top: 10px;
  text-align: right;
}

.qa-answer {
  margin-top: 20px;
}

.qa-answer-content {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.qa-answer-content.markdown-body >>> h1,
.qa-answer-content.markdown-body >>> h2,
.qa-answer-content.markdown-body >>> h3 {
  margin: 0.6em 0 0.35em;
  font-weight: 600;
}

.qa-answer-content.markdown-body >>> h1 {
  font-size: 1.25em;
}

.qa-answer-content.markdown-body >>> h2 {
  font-size: 1.15em;
}

.qa-answer-content.markdown-body >>> h3 {
  font-size: 1.05em;
}

.qa-answer-content.markdown-body >>> p {
  margin: 0.4em 0;
}

.qa-answer-content.markdown-body >>> ul,
.qa-answer-content.markdown-body >>> ol {
  margin: 0.4em 0 0.4em 1.2em;
  padding: 0;
}

.qa-answer-content.markdown-body >>> code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.1em 0.35em;
  border-radius: 3px;
  font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
  font-size: 0.9em;
}

.qa-answer-content.markdown-body >>> pre {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 10px 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.qa-answer-content.markdown-body >>> pre code {
  background: transparent;
  padding: 0;
  color: inherit;
  font-size: 0.85em;
}

.qa-answer-content.markdown-body >>> blockquote {
  margin: 0.5em 0;
  padding-left: 0.75em;
  border-left: 3px solid #dcdfe6;
  color: #606266;
}

.qa-answer-content.markdown-body >>> table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
  font-size: 0.95em;
}

.qa-answer-content.markdown-body >>> th,
.qa-answer-content.markdown-body >>> td {
  border: 1px solid #dcdfe6;
  padding: 6px 10px;
  text-align: left;
}

.qa-answer-content.markdown-body >>> th {
  background: #ebeef5;
}
</style>

