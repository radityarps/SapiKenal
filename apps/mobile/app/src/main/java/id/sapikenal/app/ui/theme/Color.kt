package id.sapikenal.app.ui.theme

import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

/**
 * SapiKenal "Bold Agricultural" palette.
 *
 * Design intent: confident, grounded, high-contrast.
 * Works outdoors in direct sunlight. Feels intentional, not template-generated.
 */
object SapiKenalColors {
    // ── Primary: Sage Green ─────────────────────────────────────────────
    val Primary = Color(0xFF466648)
    val OnPrimary = Color(0xFFFFFFFF)
    val PrimaryContainer = Color(0xFF87A987)
    val OnPrimaryContainer = Color(0xFF203E24)
    val PrimaryLight = Color(0xFF6A8E6C) // interactive hover/pressed

    // ── Secondary: Soft Brown ───────────────────────────────────────────
    val Secondary = Color(0xFF735A3A)
    val OnSecondary = Color(0xFFFFFFFF)
    val SecondaryContainer = Color(0xFFFDDAB2)
    val OnSecondaryContainer = Color(0xFF785E3E)

    // ── Tertiary: Earthy Green-Brown ────────────────────────────────────
    val Tertiary = Color(0xFF4E644F)
    val OnTertiary = Color(0xFFFFFFFF)

    // ── Background & Surface: Soft Cream ────────────────────────────────
    val Background = Color(0xFFFBF9F5)
    val OnBackground = Color(0xFF1B1C1A)
    val Surface = Color(0xFFFBF9F5)
    val OnSurface = Color(0xFF1B1C1A)
    val SurfaceVariant = Color(0xFFE4E2DE)
    val OnSurfaceVariant = Color(0xFF424841)

    // ── Text ────────────────────────────────────────────────────────────
    val TextPrimary = Color(0xFF1B1C1A) // espresso-black, warm contrast
    val TextSecondary = Color(0xFF737970) // muted grayish green

    // ── Semantic: Disease indicators (Agro-Humanist) ────────────────────
    val Healthy = Color(0xFF466648) // Sage Green — SEHAT
    val DangerPMK = Color(0xFFE2A76F) // Warm Amber/Orange — PMK
    val WarningLSD = Color(0xFFBA1A1A) // Terracotta/Red — LSD

    // ── Utility ─────────────────────────────────────────────────────────
    val Outline = Color(0xFF737970)
    val OutlineVariant = Color(0xFFC2C8BF)
    val Error = Color(0xFFBA1A1A)
    val OnError = Color(0xFFFFFFFF)
    val ErrorContainer = Color(0xFFFFDAD6)
    val OnErrorContainer = Color(0xFF93000a)

    // ── Elevation tints ─────────────────────────────────────────────────
    val SurfaceTint = Primary
}

val SapiKenalLightColorScheme =
    lightColorScheme(
        primary = SapiKenalColors.Primary,
        onPrimary = SapiKenalColors.OnPrimary,
        primaryContainer = SapiKenalColors.PrimaryContainer,
        onPrimaryContainer = SapiKenalColors.OnPrimaryContainer,
        secondary = SapiKenalColors.Secondary,
        onSecondary = SapiKenalColors.OnSecondary,
        secondaryContainer = SapiKenalColors.SecondaryContainer,
        onSecondaryContainer = SapiKenalColors.OnSecondaryContainer,
        tertiary = SapiKenalColors.Tertiary,
        onTertiary = SapiKenalColors.OnTertiary,
        background = SapiKenalColors.Background,
        onBackground = SapiKenalColors.OnBackground,
        surface = SapiKenalColors.Surface,
        onSurface = SapiKenalColors.OnSurface,
        surfaceVariant = SapiKenalColors.SurfaceVariant,
        onSurfaceVariant = SapiKenalColors.OnSurfaceVariant,
        outline = SapiKenalColors.Outline,
        outlineVariant = SapiKenalColors.OutlineVariant,
        error = SapiKenalColors.Error,
        onError = SapiKenalColors.OnError,
        errorContainer = SapiKenalColors.ErrorContainer,
        onErrorContainer = SapiKenalColors.OnErrorContainer,
        surfaceTint = SapiKenalColors.SurfaceTint,
    )

// ── Legacy alias for migration ──────────────────────────────────────────────
// Screens that still reference TropisBersihColors will compile without changes.
// Migrate them to SapiKenalColors over time.
@Deprecated("Use SapiKenalColors instead", ReplaceWith("SapiKenalColors"))
object TropisBersihColors {
    val Primary = SapiKenalColors.Primary
    val OnPrimary = SapiKenalColors.OnPrimary
    val PrimaryContainer = SapiKenalColors.PrimaryContainer
    val OnPrimaryContainer = SapiKenalColors.OnPrimaryContainer
    val Secondary = SapiKenalColors.SecondaryContainer
    val OnSecondary = SapiKenalColors.OnSecondary
    val SecondaryContainer = SapiKenalColors.SecondaryContainer
    val OnSecondaryContainer = SapiKenalColors.OnSecondaryContainer
    val Accent = SapiKenalColors.Secondary
    val Background = SapiKenalColors.Background
    val OnBackground = SapiKenalColors.OnBackground
    val Surface = SapiKenalColors.Surface
    val OnSurface = SapiKenalColors.OnSurface
    val SurfaceVariant = SapiKenalColors.SurfaceVariant
    val OnSurfaceVariant = SapiKenalColors.OnSurfaceVariant
    val TextPrimary = SapiKenalColors.TextPrimary
    val TextSecondary = SapiKenalColors.TextSecondary
    val Success = SapiKenalColors.Healthy
    val Danger = SapiKenalColors.DangerPMK
    val Warning = SapiKenalColors.WarningLSD
    val Outline = SapiKenalColors.Outline
    val OutlineVariant = SapiKenalColors.OutlineVariant
    val Error = SapiKenalColors.Error
    val OnError = SapiKenalColors.OnError
    val ErrorContainer = SapiKenalColors.ErrorContainer
    val OnErrorContainer = SapiKenalColors.OnErrorContainer
}
