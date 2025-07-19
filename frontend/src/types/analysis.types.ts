// Analysis status types
export type AnalysisStatus = 
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCESS'
  | 'FAILED'
  | 'CANCELLED'

// Analysis types
export type AnalysisType = 
  | 'full_seo'
  | 'technical_seo'
  | 'content_analysis'
  | 'performance_audit'

// Core analysis task interface
export interface AnalysisTask {
  id: string
  user_id: string
  url_analyzed: string
  status: AnalysisStatus
  analysis_type: AnalysisType
  celery_task_id?: string
  submitted_at: string
  started_at?: string
  completed_at?: string
  results?: AnalysisResults
  error_message?: string
  is_trial?: boolean
  trial_ip?: string
}

// Analysis submission interface
export interface AnalysisSubmission {
  url: string
  analysis_type: AnalysisType
  target_keywords?: string[]
  custom_config?: Record<string, any>
}

// Analysis results interface
export interface AnalysisResults {
  analysis_timestamp: string
  url: string
  analysis_type: AnalysisType
  overall_score: number
  seo_attributes: SEOAttributes
  recommendations: Recommendation[]
  warnings: Warning[]
  metadata: AnalysisMetadata
}

// SEO attributes interface
export interface SEOAttributes {
  ScoringModule: ScoringModule
  OnPageAnalyzer: OnPageAnalyzer
  TechnicalSEOAnalyzer: TechnicalSEOAnalyzer
  ContentAnalyzer: ContentAnalyzer
  PerformanceAnalyzer?: PerformanceAnalyzer
}

// Scoring module interface
export interface ScoringModule {
  overall_seo_score_percent: number
  overall_seo_score_letter: string
  category_scores: {
    on_page: number
    technical: number
    content: number
    performance?: number
  }
  score_breakdown: ScoreBreakdown[]
}

// Score breakdown interface
export interface ScoreBreakdown {
  category: string
  score: number
  max_score: number
  percentage: number
  factors: ScoreFactor[]
}

export interface ScoreFactor {
  name: string
  score: number
  weight: number
  description: string
}

// On-page analyzer interface
export interface OnPageAnalyzer {
  meta_tags: MetaTags
  heading_structure: HeadingStructure
  images: ImageAnalysis
  links: LinkAnalysis
  content_quality: ContentQuality
}

// Meta tags interface
export interface MetaTags {
  title: {
    content: string
    length: number
    is_optimal: boolean
    recommendations: string[]
  }
  description: {
    content: string
    length: number
    is_optimal: boolean
    recommendations: string[]
  }
  keywords?: {
    content: string
    recommendations: string[]
  }
  robots: {
    content: string
    is_optimal: boolean
    recommendations: string[]
  }
  canonical?: {
    url: string
    is_optimal: boolean
    recommendations: string[]
  }
  og_tags: OpenGraphTags
  twitter_cards: TwitterCards
}

// Open Graph tags interface
export interface OpenGraphTags {
  title?: string
  description?: string
  image?: string
  url?: string
  type?: string
  site_name?: string
  is_complete: boolean
  recommendations: string[]
}

// Twitter cards interface
export interface TwitterCards {
  card?: string
  title?: string
  description?: string
  image?: string
  creator?: string
  site?: string
  is_complete: boolean
  recommendations: string[]
}

// Heading structure interface
export interface HeadingStructure {
  hierarchy: HeadingLevel[]
  is_optimal: boolean
  recommendations: string[]
}

export interface HeadingLevel {
  level: number
  text: string
  count: number
}

// Image analysis interface
export interface ImageAnalysis {
  total_images: number
  images_with_alt: number
  images_without_alt: number
  large_images: number
  unoptimized_images: number
  recommendations: string[]
}

// Link analysis interface
export interface LinkAnalysis {
  internal_links: number
  external_links: number
  broken_links: number
  nofollow_links: number
  recommendations: string[]
}

// Content quality interface
export interface ContentQuality {
  word_count: number
  reading_level: string
  keyword_density: KeywordDensity[]
  content_uniqueness: number
  readability_score: number
  recommendations: string[]
}

export interface KeywordDensity {
  keyword: string
  count: number
  density: number
}

// Technical SEO analyzer interface
export interface TechnicalSEOAnalyzer {
  page_speed: PageSpeed
  mobile_friendliness: MobileFriendliness
  security: SecurityAnalysis
  crawlability: CrawlabilityAnalysis
  indexability: IndexabilityAnalysis
  structured_data: StructuredDataAnalysis
}

// Page speed interface
export interface PageSpeed {
  load_time: number
  first_contentful_paint: number
  largest_contentful_paint: number
  cumulative_layout_shift: number
  first_input_delay: number
  speed_index: number
  performance_score: number
  recommendations: string[]
}

// Mobile friendliness interface
export interface MobileFriendliness {
  is_mobile_friendly: boolean
  viewport_configured: boolean
  text_size_optimal: boolean
  touch_targets_optimal: boolean
  recommendations: string[]
}

// Security analysis interface
export interface SecurityAnalysis {
  https_enabled: boolean
  security_headers: SecurityHeaders
  mixed_content: boolean
  recommendations: string[]
}

export interface SecurityHeaders {
  strict_transport_security: boolean
  content_security_policy: boolean
  x_frame_options: boolean
  x_content_type_options: boolean
  x_xss_protection: boolean
}

// Crawlability analysis interface
export interface CrawlabilityAnalysis {
  robots_txt: RobotsTxt
  sitemap: SitemapAnalysis
  url_structure: URLStructure
  recommendations: string[]
}

export interface RobotsTxt {
  exists: boolean
  is_valid: boolean
  blocks_important_pages: boolean
  recommendations: string[]
}

export interface SitemapAnalysis {
  exists: boolean
  is_valid: boolean
  urls_count: number
  last_modified: string
  recommendations: string[]
}

export interface URLStructure {
  is_seo_friendly: boolean
  has_parameters: boolean
  is_canonical: boolean
  recommendations: string[]
}

// Indexability analysis interface
export interface IndexabilityAnalysis {
  is_indexable: boolean
  meta_robots: string
  x_robots_tag: string
  canonical_issues: boolean
  recommendations: string[]
}

// Structured data analysis interface
export interface StructuredDataAnalysis {
  schema_markup: SchemaMarkup[]
  json_ld_present: boolean
  microdata_present: boolean
  rdfa_present: boolean
  recommendations: string[]
}

export interface SchemaMarkup {
  type: string
  is_valid: boolean
  properties: Record<string, any>
  errors: string[]
}

// Content analyzer interface
export interface ContentAnalyzer {
  content_analysis: ContentAnalysisDetails
  keyword_analysis: KeywordAnalysis
  competitor_analysis?: CompetitorAnalysis
  content_gaps: ContentGap[]
}

export interface ContentAnalysisDetails {
  content_length: number
  content_structure: ContentStructure
  content_freshness: ContentFreshness
  content_relevance: number
  recommendations: string[]
}

export interface ContentStructure {
  paragraphs: number
  sentences: number
  avg_sentence_length: number
  lists: number
  tables: number
  recommendations: string[]
}

export interface ContentFreshness {
  last_modified: string
  publishing_date: string
  is_fresh: boolean
  recommendations: string[]
}

export interface KeywordAnalysis {
  target_keywords: TargetKeyword[]
  keyword_distribution: KeywordDistribution
  lsi_keywords: LSIKeyword[]
  recommendations: string[]
}

export interface TargetKeyword {
  keyword: string
  frequency: number
  density: number
  prominence: number
  is_optimal: boolean
}

export interface KeywordDistribution {
  in_title: number
  in_headings: number
  in_content: number
  in_alt_text: number
  in_meta_description: number
}

export interface LSIKeyword {
  keyword: string
  relevance: number
  frequency: number
}

export interface CompetitorAnalysis {
  competitors: Competitor[]
  competitive_keywords: CompetitiveKeyword[]
  content_gap_analysis: ContentGap[]
}

export interface Competitor {
  url: string
  domain_authority: number
  content_length: number
  target_keywords: string[]
  strengths: string[]
  weaknesses: string[]
}

export interface CompetitiveKeyword {
  keyword: string
  your_position: number
  competitor_position: number
  difficulty: number
  opportunity: number
}

export interface ContentGap {
  topic: string
  keywords: string[]
  opportunity_score: number
  recommended_content_type: string
}

// Performance analyzer interface
export interface PerformanceAnalyzer {
  core_web_vitals: CoreWebVitals
  resource_analysis: ResourceAnalysis
  caching_analysis: CachingAnalysis
  optimization_opportunities: OptimizationOpportunity[]
}

export interface CoreWebVitals {
  largest_contentful_paint: number
  first_input_delay: number
  cumulative_layout_shift: number
  first_contentful_paint: number
  speed_index: number
  time_to_interactive: number
  total_blocking_time: number
}

export interface ResourceAnalysis {
  total_resources: number
  resource_breakdown: ResourceBreakdown[]
  largest_resources: LargestResource[]
  unused_resources: UnusedResource[]
}

export interface ResourceBreakdown {
  type: string
  count: number
  total_size: number
  average_size: number
}

export interface LargestResource {
  url: string
  type: string
  size: number
  load_time: number
}

export interface UnusedResource {
  url: string
  type: string
  size: number
  coverage: number
}

export interface CachingAnalysis {
  cache_policy: CachePolicy[]
  cdn_usage: CDNUsage
  browser_caching: BrowserCaching
  recommendations: string[]
}

export interface CachePolicy {
  resource_type: string
  cache_duration: number
  is_optimal: boolean
}

export interface CDNUsage {
  is_using_cdn: boolean
  cdn_provider: string
  geographic_distribution: string[]
  recommendations: string[]
}

export interface BrowserCaching {
  static_resources_cached: boolean
  cache_headers_present: boolean
  cache_duration: number
  recommendations: string[]
}

export interface OptimizationOpportunity {
  category: string
  impact: 'high' | 'medium' | 'low'
  effort: 'high' | 'medium' | 'low'
  description: string
  potential_savings: string
  implementation_guide: string
}

// Recommendations and warnings
export interface Recommendation {
  category: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  effort: string
  implementation_guide: string
  resources: RecommendationResource[]
}

export interface RecommendationResource {
  title: string
  url: string
  type: 'documentation' | 'tool' | 'guide' | 'video'
}

export interface Warning {
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  resolution: string
}

// Analysis metadata
export interface AnalysisMetadata {
  user_agent: string
  screen_resolution: string
  analysis_duration: number
  modules_executed: string[]
  errors_encountered: string[]
  configuration: AnalysisConfiguration
}

export interface AnalysisConfiguration {
  timeout: number
  follow_redirects: boolean
  javascript_enabled: boolean
  mobile_simulation: boolean
  location: string
  custom_headers: Record<string, string>
}

// Analysis filters and pagination
export interface AnalysisFilters {
  status: AnalysisStatus | null
  analysisType: AnalysisType | null
  dateRange: DateRange | null
  page: number
  pageSize: number
}

export interface DateRange {
  start: string
  end: string
}

export interface PaginatedAnalyses {
  items: AnalysisTask[]
  total: number
  page: number
  pageSize: number
  pages: number
}

// Analysis status response
export interface AnalysisStatusResponse {
  analysis_id: string
  status: AnalysisStatus
  progress_percentage: number
  submitted_at: string
  started_at?: string
  completed_at?: string
  estimated_completion?: string
  error_message?: string
  celery_task_id?: string
}

// Batch analysis request
export interface BatchAnalysisRequest {
  urls: string[]
  analysis_type: AnalysisType
  target_keywords?: string[]
  custom_config?: Record<string, any>
}

// Export formats
export type ExportFormat = 'pdf' | 'csv' | 'json' | 'html'

export interface ExportRequest {
  analysis_id: string
  format: ExportFormat
  sections?: string[]
  template?: string
}

// Analysis comparison
export interface AnalysisComparison {
  baseline: AnalysisTask
  comparison: AnalysisTask
  differences: ComparisonDifference[]
  improvements: ComparisonImprovement[]
  regressions: ComparisonRegression[]
}

export interface ComparisonDifference {
  metric: string
  baseline_value: number
  comparison_value: number
  change_percentage: number
  change_type: 'improvement' | 'regression' | 'neutral'
}

export interface ComparisonImprovement {
  metric: string
  improvement_percentage: number
  description: string
}

export interface ComparisonRegression {
  metric: string
  regression_percentage: number
  description: string
  suggested_actions: string[]
}

// Scheduled analysis
export interface ScheduledAnalysis {
  id: string
  user_id: string
  url: string
  analysis_type: AnalysisType
  frequency: 'daily' | 'weekly' | 'monthly'
  next_run: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// Analysis trends
export interface AnalysisTrend {
  metric: string
  timespan: string
  data_points: TrendDataPoint[]
  trend_direction: 'up' | 'down' | 'stable'
  trend_percentage: number
}

export interface TrendDataPoint {
  date: string
  value: number
  analysis_id: string
}