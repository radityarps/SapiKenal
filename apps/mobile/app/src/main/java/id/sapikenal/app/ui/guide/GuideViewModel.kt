package id.sapikenal.app.ui.guide

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class SyncStatus {
    IDLE,
    SYNCING,
    SUCCESS,
    FAILURE,
}

@HiltViewModel
class GuideViewModel
    @Inject
    constructor(
        private val repository: GuideRepository,
    ) : ViewModel() {
        val searchQuery = MutableStateFlow("")
        val selectedCategory = MutableStateFlow<GuideCategory?>(null)
        val isRefreshing = MutableStateFlow(false)

        private val _syncStatus = MutableStateFlow(SyncStatus.IDLE)
        val syncStatus: StateFlow<SyncStatus> = _syncStatus.asStateFlow()

        private var syncFeedbackJob: Job? = null

        private val articles = repository.articles()

        val filteredArticles: StateFlow<List<GuideArticle>> =
            combine(articles, searchQuery, selectedCategory) { items, query, category ->
                items.filter { article ->
                    val matchesQuery =
                        query.isBlank() ||
                            article.title.contains(query, ignoreCase = true) ||
                            article.summary.contains(query, ignoreCase = true) ||
                            article.body.contains(query, ignoreCase = true)
                    matchesQuery && (category == null || article.category == category)
                }
            }.stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = emptyList(),
            )

        fun loadArticles() {
            refreshArticles()
        }

        fun refreshArticles() {
            viewModelScope.launch {
                syncFeedbackJob?.cancel()
                isRefreshing.value = true
                _syncStatus.value = SyncStatus.SYNCING
                val result = repository.refresh()
                isRefreshing.value = false

                if (result.isSuccess) {
                    _syncStatus.value = SyncStatus.SUCCESS
                } else {
                    _syncStatus.value = SyncStatus.FAILURE
                }

                syncFeedbackJob =
                    launch {
                        delay(3_000)
                        _syncStatus.value = SyncStatus.IDLE
                    }
            }
        }

        fun onSearchQueryChange(query: String) {
            searchQuery.value = query
        }

        fun onCategoryFilter(category: GuideCategory?) {
            selectedCategory.value = category
        }
    }
