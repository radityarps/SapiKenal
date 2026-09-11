package id.sapikenal.app.ui.guide

import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class GuideDetailViewModel
    @Inject
    constructor(
        private val repository: GuideRepository,
    ) : ViewModel() {
        fun article(
            locale: String,
            articleKey: String,
        ): Flow<GuideArticle?> = repository.article(locale, articleKey)
    }
