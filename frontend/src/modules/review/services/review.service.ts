import { getQuestionById } from '@/modules/question/services/question.service'
import type { PracticeReportRecord } from '../types/review'

const mockReports: PracticeReportRecord[] = [
  {
    id: 'demo-101',
    questionId: 101,
    questionTitle: '基层治理中的“最后一公里”协同',
    questionType: '概括题',
    source: '2024 国考副省',
    createdAt: '2026-04-21 20:15',
    totalScore: 74,
    provider: 'OpenAI',
    model: 'gpt-4.1-mini',
    overallComment: '问题抓得准，但措施还不够实。',
    strengths: ['能快速提炼三类堵点。', '结构基本清楚。'],
    issues: ['建议偏原则。', '问题和措施还不够对位。'],
    suggestions: ['按“问题-原因-措施”重排。', '多用可执行表达。'],
    dimensions: [
      { name: '审题与任务回应', score: 17, maxScore: 20, comment: '回应完整，措施偏粗。' },
      { name: '结构组织', score: 18, maxScore: 25, comment: '结构清楚，承接可更紧。' },
      { name: '表达与概括', score: 21, maxScore: 25, comment: '概括较稳。' },
      { name: '内容深度', score: 18, maxScore: 30, comment: '能指出问题，归因还可更深。' },
    ],
    paragraphReviews: [
      {
        id: 'p1',
        title: '首段概括',
        excerpt: '基层治理协同中存在信息重复填写、部门之间沟通不畅等问题。',
        issue: '列举直接，概念不够收束。',
        suggestion: '先总写，再展开表现。',
      },
      {
        id: 'p2',
        title: '措施段',
        excerpt: '要加强平台建设，提升服务水平，完善监督机制。',
        issue: '表述偏空。',
        suggestion: '补足动作和对象。',
      },
    ],
    answers: {
      a1: '基层治理协同中主要存在信息重复采集、部门之间共享不畅、办理进度透明度不高等问题。',
      a2: '应统一表单入口，建设共享平台，明确部门责任，完善反馈闭环。',
    },
    answerText: '基层治理协同中主要存在信息重复采集、部门之间共享不畅、办理进度透明度不高等问题。应统一表单入口，建设共享平台，明确部门责任，完善反馈闭环。',
    referenceAnswer: getQuestionById(101)?.referenceAnswer ?? '',
    optimizedExample: getQuestionById(101)?.optimizedExample ?? '',
  },
  {
    id: 'demo-102',
    questionId: 102,
    questionTitle: '夜间经济如何兼顾活力与秩序',
    questionType: '对策题',
    source: '平台模拟卷 A',
    createdAt: '2026-04-20 18:40',
    totalScore: 79,
    provider: 'DeepSeek',
    model: 'deepseek-chat',
    overallComment: '框架成熟，但对策还可更细。',
    strengths: ['分论点清楚。', '对精细化治理理解到位。'],
    issues: ['个别对策还像口号。', '结尾回扣不够。'],
    suggestions: ['补充分时分区、保洁和投诉闭环。', '结尾再点明平衡关系。'],
    dimensions: [
      { name: '任务回应', score: 18, maxScore: 20, comment: '回应完整。' },
      { name: '结构组织', score: 20, maxScore: 25, comment: '层次自然。' },
      { name: '语言表达', score: 20, maxScore: 25, comment: '表达较稳。' },
      { name: '措施落地性', score: 21, maxScore: 30, comment: '有执行意识，但还可更细。' },
    ],
    paragraphReviews: [
      {
        id: 'p1',
        title: '总论点段',
        excerpt: '夜间经济要在活力和秩序之间形成动态平衡。',
        issue: '承接句偏少。',
        suggestion: '补一句平衡原因。',
      },
    ],
    answers: {
      a1: '夜间经济发展的矛盾在于消费活力与城市秩序之间的张力。',
      a2: '要坚持分区管理、完善配套服务、建立联动治理机制。',
    },
    answerText: '夜间经济发展的矛盾在于消费活力与城市秩序之间的张力。要坚持分区管理、完善配套服务、建立联动治理机制。',
    referenceAnswer: getQuestionById(102)?.referenceAnswer ?? '',
    optimizedExample: getQuestionById(102)?.optimizedExample ?? '',
  },
]

export function listMockReports() {
  return mockReports
}

export function getReportById(reportId: string) {
  return mockReports.find((item) => item.id === reportId) ?? null
}

export function getLatestReportForQuestion(questionId: number) {
  return mockReports.find((item) => item.questionId === questionId) ?? null
}
