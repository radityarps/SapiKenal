package id.sapikenal.app.ui.guide

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class GuideViewModel
    @Inject
    constructor(
        private val repository: GuideRepository,
    ) : ViewModel() {
        private val locale = MutableStateFlow("id-ID")
        val searchQuery = MutableStateFlow("")
        val selectedCategory = MutableStateFlow<GuideCategory?>(null)

        private val articles = locale.flatMapLatest(repository::articles)

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

        fun loadArticles(context: Context) {
            val target = context.guideLocale()
            locale.value = target
            viewModelScope.launch { repository.refresh(target) }
        }

        fun onSearchQueryChange(query: String) {
            searchQuery.value = query
        }

        fun onCategoryFilter(category: GuideCategory?) {
            selectedCategory.value = category
        }
    }

internal fun Context.guideLocale(): String =
    if (resources.configuration.locales[0]
            .language
            .equals("en", ignoreCase = true)
    ) {
        "en-US"
    } else {
        "id-ID"
    }
