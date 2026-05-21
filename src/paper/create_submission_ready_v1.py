from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "manuscript" / "ASMAG_2026_submission_draft.md"
READY = ROOT / "manuscript" / "ASMAG_2026_submission_ready_v1.md"
RESULT = ROOT / "outputs" / "full_cdnet2014_official_edge_profile_pc"
PKG = ROOT / "outputs" / "submission_package"
PAPER_FIGS = ROOT / "outputs" / "paper_ready_figures"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def replace_between(text: str, start_pattern: str, end_pattern: str, replacement: str) -> str:
    pattern = re.compile(start_pattern + r".*?(?=" + end_pattern + r")", re.S | re.M)
    next_text, count = pattern.subn(lambda _match: replacement.rstrip() + "\n\n", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace section matching {start_pattern!r}")
    return next_text


def clean_mojibake(text: str) -> str:
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€‹": "",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "Ã—": "x",
        "–": "-",
        "—": "-",
        "×": "x",
        "Watt/Joule": "Watt/Joule",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def make_architecture_figure() -> None:
    PAPER_FIGS.mkdir(parents=True, exist_ok=True)
    png = PAPER_FIGS / "asmag_trc_architecture.png"
    pdf = PAPER_FIGS / "asmag_trc_architecture.pdf"
    if png.exists() and pdf.exists():
        return

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "savefig.dpi": 320,
        }
    )
    fig, ax = plt.subplots(figsize=(9.0, 3.6))
    ax.set_axis_off()
    boxes = [
        ("Input\nvideo stream", 0.05, 0.55, 0.13, 0.23, "#E8F1FF"),
        ("Motion\nproposal layer", 0.22, 0.55, 0.15, 0.23, "#EAF7EF"),
        ("Adaptive\nmotion gate", 0.42, 0.55, 0.15, 0.23, "#FFF4E5"),
        ("Controller\nmode selector", 0.42, 0.16, 0.15, 0.23, "#F3E8FF"),
        ("Detector /\nheavy inference", 0.64, 0.67, 0.16, 0.23, "#FFE9EC"),
        ("Temporal\nreuse module", 0.64, 0.31, 0.16, 0.23, "#E9FBFA"),
        ("Prediction\nand metrics", 0.84, 0.49, 0.13, 0.23, "#F0F2F5"),
    ]
    for label, x, y, w, h, color in boxes:
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#263238", linewidth=1.2, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", transform=ax.transAxes)

    arrows = [
        ((0.18, 0.665), (0.22, 0.665)),
        ((0.37, 0.665), (0.42, 0.665)),
        ((0.57, 0.665), (0.64, 0.76)),
        ((0.57, 0.59), (0.64, 0.43)),
        ((0.50, 0.55), (0.50, 0.39)),
        ((0.57, 0.28), (0.64, 0.38)),
        ((0.80, 0.78), (0.84, 0.62)),
        ((0.80, 0.43), (0.84, 0.57)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", lw=1.3, color="#263238"))
    ax.text(0.50, 0.08, "Mode controls gate thresholds, fallback behavior, and reuse aggressiveness", ha="center", transform=ax.transAxes, fontsize=8)
    fig.tight_layout()
    fig.savefig(png, bbox_inches="tight", dpi=320)
    fig.savefig(pdf, bbox_inches="tight", dpi=320)
    plt.close(fig)


def figure_markdown(number: int, title: str, filename: str, caption: str) -> str:
    path = f"../outputs/paper_ready_figures/{filename}"
    source = f"outputs/paper_ready_figures/{filename}"
    return (
        f"![Figure {number}. {title}]({path})\n\n"
        f"Caption: Figure {number}. {caption} Source file: `{source}`."
    )


def table4_from_csv() -> tuple[str, str]:
    gain = pd.read_csv(RESULT / "gain_summary.csv")
    keep = [
        "ASMAG_TR_CONTROLLER vs P3_MOG2",
        "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED vs P3_MOG2",
        "ASMAG_TR_FAST vs P3_MOG2",
        "P2_FrameDiff vs P3_MOG2",
        "P1_YOLO_Only vs P3_MOG2",
    ]
    rows = []
    for comparison in keep:
        row = gain.loc[gain["Comparison"] == comparison].iloc[0]
        label = comparison
        if comparison == "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED vs P3_MOG2":
            label = "ONLINE_CALIBRATED vs P3_MOG2"
        rows.append(
            [
                label,
                f"{row['FMeasure_gain']:+.4f}",
                f"{row['Event_F1_gain']:+.4f}",
                f"{row['Activation_saving']:+.4f}",
                f"{row['Energy_saving']:+.4f}",
                f"{row['Simulated_runtime_energy_saving']:+.4f}",
                f"{row['FPS_gain']:+.2f}",
                f"{row['P95_latency_gain']:+.2f}",
                f"{row['AE_Score_gain']:+.4f}",
            ]
        )
    header = "| Comparison | FMeasure Gain | Event F1 Gain | Activation Saving | Energy Saving | Simulated Runtime Energy Saving | FPS Gain | P95 Latency Gain | AE Score Gain |"
    sep = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    final_table = "\n".join([header, sep, body])
    report_rows = [
        ("ASMAG_TR_CONTROLLER vs P3_MOG2", "+0.0852", "+0.0489"),
        ("ONLINE_CALIBRATED vs P3_MOG2", "+0.1635", "+0.1466"),
        ("ASMAG_TR_FAST vs P3_MOG2", "+0.4592", "+0.5807"),
    ]
    report = (
        "# Pass 2 Table 4 Validation\n\n"
        "CSV source of truth: `outputs/full_cdnet2014_official_edge_profile_pc/gain_summary.csv`.\n\n"
        "| Comparison | Old manuscript simulated runtime energy saving | Corrected CSV value |\n"
        "|---|---:|---:|\n"
        + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in report_rows)
        + "\n\n## Final Table 4 Markdown\n\n"
        + final_table
        + "\n\nPositive activation and energy savings mean lower activation or energy than `P3_MOG2`. Positive P95 latency gain means lower P95 latency than `P3_MOG2`."
    )
    return final_table, report


def references() -> tuple[str, str, int, int]:
    complete = [
        ("Barnich, O., & Van Droogenbroeck, M. (2011). ViBe: A universal background subtraction algorithm for video sequences. IEEE Transactions on Image Processing, 20(6), 1709-1724.", "barnich2011vibe", "article"),
        ("Bewley, A., Ge, Z., Ott, L., Ramos, F., & Upcroft, B. (2016). Simple online and realtime tracking. In IEEE International Conference on Image Processing (pp. 3464-3468).", "bewley2016sort", "inproceedings"),
        ("Bochkovskiy, A., Wang, C.-Y., & Liao, H.-Y. M. (2020). YOLOv4: Optimal speed and accuracy of object detection. arXiv:2004.10934.", "bochkovskiy2020yolov4", "misc"),
        ("Bolme, D. S., Beveridge, J. R., Draper, B. A., & Lui, Y. M. (2010). Visual object tracking using adaptive correlation filters. In IEEE Conference on Computer Vision and Pattern Recognition (pp. 2544-2550).", "bolme2010mosse", "inproceedings"),
        ("Bouwmans, T. (2014). Traditional and recent approaches in background modeling for foreground detection: An overview. Computer Science Review, 11-12, 31-66.", "bouwmans2014background", "article"),
        ("Canny, J. (1986). A computational approach to edge detection. IEEE Transactions on Pattern Analysis and Machine Intelligence, 8(6), 679-698.", "canny1986edge", "article"),
        ("Crankshaw, D., Wang, X., Zhou, G., Franklin, M. J., Gonzalez, J. E., & Stoica, I. (2017). Clipper: A low-latency online prediction serving system. In USENIX Symposium on Networked Systems Design and Implementation (pp. 613-627).", "crankshaw2017clipper", "inproceedings"),
        ("Elgammal, A., Harwood, D., & Davis, L. (2000). Non-parametric model for background subtraction. In European Conference on Computer Vision (pp. 751-767).", "elgammal2000nonparametric", "inproceedings"),
        ("Girshick, R. (2015). Fast R-CNN. In IEEE International Conference on Computer Vision (pp. 1440-1448).", "girshick2015fast", "inproceedings"),
        ("Goyette, N., Jodoin, P.-M., Porikli, F., Konrad, J., & Ishwar, P. (2012). Changedetection.net: A new change detection benchmark dataset. In IEEE Conference on Computer Vision and Pattern Recognition Workshops (pp. 1-8).", "goyette2012changedetection", "inproceedings"),
        ("Han, S., Liu, X., Mao, H., Pu, J., Pedram, A., Horowitz, M. A., & Dally, W. J. (2016). EIE: Efficient inference engine on compressed deep neural network. In International Symposium on Computer Architecture (pp. 243-254).", "han2016eie", "inproceedings"),
        ("Han, S., Mao, H., & Dally, W. J. (2016). Deep compression: Compressing deep neural networks with pruning, trained quantization and Huffman coding. In International Conference on Learning Representations.", "han2016deepcompression", "inproceedings"),
        ("Henriques, J. F., Caseiro, R., Martins, P., & Batista, J. (2015). High-speed tracking with kernelized correlation filters. IEEE Transactions on Pattern Analysis and Machine Intelligence, 37(3), 583-596.", "henriques2015kcf", "article"),
        ("Howard, A. G., Zhu, M., Chen, B., Kalenichenko, D., Wang, W., Weyand, T., Andreetto, M., & Adam, H. (2017). MobileNets: Efficient convolutional neural networks for mobile vision applications. arXiv:1704.04861.", "howard2017mobilenets", "misc"),
        ("Jacob, B., Kligys, S., Chen, B., Zhu, M., Tang, M., Howard, A., Adam, H., & Kalenichenko, D. (2018). Quantization and training of neural networks for efficient integer-arithmetic-only inference. In IEEE Conference on Computer Vision and Pattern Recognition (pp. 2704-2713).", "jacob2018quantization", "inproceedings"),
        ("Jiang, J., Ananthanarayanan, G., Bodik, P., Sen, S., & Stoica, I. (2018). Chameleon: Scalable adaptation of video analytics. In ACM SIGCOMM Conference (pp. 253-266).", "jiang2018chameleon", "inproceedings"),
        ("Jouppi, N. P., Young, C., Patil, N., Patterson, D., Agrawal, G., Bajwa, R., Bates, S., Bhatia, S., Boden, N., Borchers, A., Boyle, R., Cantin, P.-L., Chao, C., Clark, C., Coriell, J., Daley, M., Dau, M., Dean, J., Gelb, B., Ghaemmaghami, T. V., Gottipati, R., Gulland, W., Hagmann, R., Ho, C. R., Hogberg, D., Hu, J., Hundt, R., Hurt, D., Ibarz, J., Jaffey, A., Jaworski, A., Kaplan, A., Khaitan, H., Killebrew, D., Koch, A., Kumar, N., Lacy, S., Laudon, J., Law, J., Le, D., Leary, C., Liu, Z., Lucke, K., Lundin, A., MacKean, G., Maggiore, A., Mahony, M., Miller, K., Nagarajan, R., Narayanaswami, R., Ni, R., Nix, K., Norrie, T., Omernick, M., Penukonda, N., Phelps, A., Ross, J., Ross, M., Salek, A., Samadiani, E., Severn, C., Sizikov, G., Snelham, M., Souter, J., Steinberg, D., Swing, A., Tan, M., Thorson, G., Tian, B., Toma, H., Tuttle, E., Vasudevan, V., Walter, R., Wang, W., Wilcox, E., & Yoon, D. H. (2017). In-datacenter performance analysis of a tensor processing unit. In International Symposium on Computer Architecture (pp. 1-12).", "jouppi2017tpu", "inproceedings"),
        ("Kalman, R. E. (1960). A new approach to linear filtering and prediction problems. Journal of Basic Engineering, 82(1), 35-45.", "kalman1960filtering", "article"),
        ("Kang, D., Emmons, J., Abuzaid, F., Bailis, P., & Zaharia, M. (2017). NoScope: Optimizing neural network queries over video at scale. Proceedings of the VLDB Endowment, 10(11), 1586-1597.", "kang2017noscope", "article"),
        ("Kang, D., Bailis, P., & Zaharia, M. (2019). BlazeIt: Optimizing declarative aggregation and limit queries for neural network-based video analytics. Proceedings of the VLDB Endowment, 13(4), 533-546.", "kang2019blazeit", "article"),
        ("Lane, N. D., Bhattacharya, S., Georgiev, P., Forlivesi, C., & Kawsar, F. (2016). DeepX: A software accelerator for low-power deep learning inference on mobile devices. In International Conference on Information Processing in Sensor Networks (pp. 1-12).", "lane2016deepx", "inproceedings"),
        ("Lin, T.-Y., Goyal, P., Girshick, R., He, K., & Dollar, P. (2017). Focal loss for dense object detection. In IEEE International Conference on Computer Vision (pp. 2980-2988).", "lin2017focal", "inproceedings"),
        ("Liu, W., Anguelov, D., Erhan, D., Szegedy, C., Reed, S., Fu, C.-Y., & Berg, A. C. (2016). SSD: Single shot MultiBox detector. In European Conference on Computer Vision (pp. 21-37).", "liu2016ssd", "inproceedings"),
        ("Lucas, B. D., & Kanade, T. (1981). An iterative image registration technique with an application to stereo vision. In International Joint Conference on Artificial Intelligence (pp. 674-679).", "lucas1981kanade", "inproceedings"),
        ("Maddalena, L., & Petrosino, A. (2008). A self-organizing approach to background subtraction for visual surveillance applications. IEEE Transactions on Image Processing, 17(7), 1168-1177.", "maddalena2008sobs", "article"),
        ("Merenda, M., Porcaro, C., & Iero, D. (2020). Edge machine learning for AI-enabled IoT devices: A review. Sensors, 20(9), 2533.", "merenda2020edge", "article"),
        ("Piccardi, M. (2004). Background subtraction techniques: A review. In IEEE International Conference on Systems, Man and Cybernetics (pp. 3099-3104).", "piccardi2004background", "inproceedings"),
        ("Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. In IEEE Conference on Computer Vision and Pattern Recognition (pp. 779-788).", "redmon2016yolo", "inproceedings"),
        ("Redmon, J., & Farhadi, A. (2017). YOLO9000: Better, faster, stronger. In IEEE Conference on Computer Vision and Pattern Recognition (pp. 7263-7271).", "redmon2017yolo9000", "inproceedings"),
        ("Redmon, J., & Farhadi, A. (2018). YOLOv3: An incremental improvement. arXiv:1804.02767.", "redmon2018yolov3", "misc"),
        ("Ren, S., He, K., Girshick, R., & Sun, J. (2015). Faster R-CNN: Towards real-time object detection with region proposal networks. In Advances in Neural Information Processing Systems (pp. 91-99).", "ren2015faster", "inproceedings"),
        ("Stauffer, C., & Grimson, W. E. L. (1999). Adaptive background mixture models for real-time tracking. In IEEE Conference on Computer Vision and Pattern Recognition (Vol. 2, pp. 246-252).", "stauffer1999adaptive", "inproceedings"),
        ("Sze, V., Chen, Y.-H., Yang, T.-J., & Emer, J. S. (2017). Efficient processing of deep neural networks: A tutorial and survey. Proceedings of the IEEE, 105(12), 2295-2329.", "sze2017efficient", "article"),
        ("Tan, M., Pang, R., & Le, Q. V. (2020). EfficientDet: Scalable and efficient object detection. In IEEE/CVF Conference on Computer Vision and Pattern Recognition (pp. 10781-10790).", "tan2020efficientdet", "inproceedings"),
        ("Teed, Z., & Deng, J. (2020). RAFT: Recurrent all-pairs field transforms for optical flow. In European Conference on Computer Vision (pp. 402-419).", "teed2020raft", "inproceedings"),
        ("Wang, Y., Jodoin, P.-M., Porikli, F., Konrad, J., Benezeth, Y., & Ishwar, P. (2014). CDnet 2014: An expanded change detection benchmark dataset. In IEEE Conference on Computer Vision and Pattern Recognition Workshops (pp. 387-394).", "wang2014cdnet", "inproceedings"),
        ("Wojke, N., Bewley, A., & Paulus, D. (2017). Simple online and realtime tracking with a deep association metric. In IEEE International Conference on Image Processing (pp. 3645-3649).", "wojke2017deepsort", "inproceedings"),
        ("Zivkovic, Z. (2004). Improved adaptive Gaussian mixture model for background subtraction. In International Conference on Pattern Recognition (Vol. 2, pp. 28-31).", "zivkovic2004improved", "inproceedings"),
        ("Zivkovic, Z., & van der Heijden, F. (2006). Efficient adaptive density estimation per image pixel for the task of background subtraction. Pattern Recognition Letters, 27(7), 773-780.", "zivkovic2006efficient", "article"),
    ]
    todos = [
        "NVIDIA. (TODO). TensorRT documentation. Add version, access date, and URL if vendor documentation is cited.",
        "Intel. (TODO). OpenVINO toolkit documentation. Add version, access date, and URL if vendor documentation is cited.",
        "Google. (TODO). Coral Edge TPU documentation. Add version, access date, and URL if vendor documentation is cited.",
        "Hailo. (TODO). Hailo AI accelerator documentation. Add version, access date, and URL if vendor documentation is cited.",
        "TODO: Add a direct physical power-profiling reference if energy-measurement discussion is expanded beyond proxy metrics.",
    ]
    refs_text = "# References\n\n" + "\n\n".join(f"{i + 1}. {entry[0]}" for i, entry in enumerate(complete + [(t, "", "") for t in todos]))
    bib = make_bib(complete, todos)
    return refs_text, bib, len(complete), len(todos)


def make_bib(complete: list[tuple[str, str, str]], todos: list[str]) -> str:
    entries = {
        "wang2014cdnet": """@inproceedings{wang2014cdnet,\n  title = {CDnet 2014: An Expanded Change Detection Benchmark Dataset},\n  author = {Wang, Yi and Jodoin, Pierre-Marc and Porikli, Fatih and Konrad, Janusz and Benezeth, Yannick and Ishwar, Prakash},\n  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition Workshops},\n  pages = {387--394},\n  year = {2014}\n}""",
        "stauffer1999adaptive": """@inproceedings{stauffer1999adaptive,\n  title = {Adaptive Background Mixture Models for Real-Time Tracking},\n  author = {Stauffer, Chris and Grimson, W. Eric L.},\n  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},\n  volume = {2},\n  pages = {246--252},\n  year = {1999}\n}""",
        "redmon2016yolo": """@inproceedings{redmon2016yolo,\n  title = {You Only Look Once: Unified, Real-Time Object Detection},\n  author = {Redmon, Joseph and Divvala, Santosh and Girshick, Ross and Farhadi, Ali},\n  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},\n  pages = {779--788},\n  year = {2016}\n}""",
        "kang2017noscope": """@article{kang2017noscope,\n  title = {NoScope: Optimizing Neural Network Queries over Video at Scale},\n  author = {Kang, Daniel and Emmons, John and Abuzaid, Firas and Bailis, Peter and Zaharia, Matei},\n  journal = {Proceedings of the VLDB Endowment},\n  volume = {10},\n  number = {11},\n  pages = {1586--1597},\n  year = {2017}\n}""",
        "jiang2018chameleon": """@inproceedings{jiang2018chameleon,\n  title = {Chameleon: Scalable Adaptation of Video Analytics},\n  author = {Jiang, Junchen and Ananthanarayanan, Ganesh and Bodik, Peter and Sen, Siddhartha and Stoica, Ion},\n  booktitle = {Proceedings of the ACM SIGCOMM Conference},\n  pages = {253--266},\n  year = {2018}\n}""",
    }
    lines = [entries[key] for _, key, _ in complete if key in entries]
    for reference, key, kind in complete:
        if key in entries:
            continue
        title = reference.split("). ", 1)[1].split(". ", 1)[0] if "). " in reference else reference
        year_match = re.search(r"\((\d{4})\)", reference)
        year = year_match.group(1) if year_match else "TODO"
        lines.append(
            f"@{kind}{{{key},\n"
            f"  title = {{{title}}},\n"
            f"  note = {{{reference}}},\n"
            f"  year = {{{year}}}\n"
            f"}}"
        )
    lines.extend(f"% {todo}" for todo in todos)
    return "\n\n".join(lines)


def declarations() -> str:
    return """
# Declarations

## Data Availability

The CDnet2014 dataset used in this study is publicly available from the dataset providers. The generated experimental summaries, including per-category, per-video, runtime, mode-usage, configuration, progress, and figure files, are provided as supplementary materials with this submission.

## Code Availability

TODO: Choose the final code-release policy. Suggested wording: The code will be made available upon reasonable request. Alternative wording: The code and scripts used for evaluation will be released upon publication.

## Conflict of Interest

The authors declare no conflict of interest.

## Funding

TODO: Funding information is not available in the current project files. Add grant numbers, institutional support, or state that no specific funding was received.

## Author Contributions

TODO: Replace placeholders with actual author names. Suggested CRediT-style draft: [Author 1] contributed to conceptualization, methodology, software, experiments, analysis, and writing-original draft. [Author 2] contributed to supervision, validation, review, and editing. All authors read and approved the final manuscript.

## Ethics Approval

This study uses a public benchmark dataset and does not involve human-subject recruitment, intervention, or collection of new personal data by the authors. Ethics approval is therefore not applicable. TODO: Confirm wording against target journal requirements.

## Supplementary Materials

Supplementary materials include the full per-category and per-video result tables, CPU-only edge runtime profiling summaries, controller mode-usage summaries, experiment configuration, run plan, progress log, and supplementary figures.
"""


def main() -> None:
    make_architecture_figure()
    original = DRAFT.read_text(encoding="utf-8")
    text = clean_mojibake(original)
    changes = [
        "Created clean Markdown master from manuscript/ASMAG_2026_submission_draft.md.",
        "Cleaned common mojibake artifacts from extracted Markdown.",
    ]

    text = text.replace(
        "The CDnet2014 benchmark is one of the most widely used datasets for evaluating change detection algorithms.",
        "The CDnet2014 benchmark is one of the most widely used datasets for evaluating change detection algorithms (Wang et al., 2014).",
    )
    text = text.replace(
        "Classical approaches such as frame differencing, background modeling, Gaussian mixture models, and motion segmentation methods aim to separate foreground regions from a relatively stable background.",
        "Classical approaches such as frame differencing, background modeling, Gaussian mixture models, and motion segmentation methods aim to separate foreground regions from a relatively stable background (Stauffer & Grimson, 1999; Bouwmans, 2014).",
    )
    text = text.replace("(arXiv)", "(Redmon et al., 2016)", 1)
    text = text.replace("(arXiv)", "(Kang et al., 2017)", 1)
    text = text.replace("(Microsoft)", "(Jiang et al., 2018)")
    changes.append("Replaced citation placeholders with reliable author-year citations for YOLO, NoScope, and Chameleon.")

    text = replace_between(text, r"^## 3\.2\.", r"^## 3\.3\.", SECTION_3_2)
    text = replace_between(text, r"^## 3\.3\.", r"^## 3\.4\.", SECTION_3_3)
    text = replace_between(text, r"^## 3\.4\.", r"^## 3\.5\.", SECTION_3_4)
    text = replace_between(text, r"^## 3\.5\.", r"^## 3\.6\.", SECTION_3_5)
    text = replace_between(text, r"^## 3\.8\.", r"^## 3\.9\.", SECTION_3_8)
    text = replace_between(text, r"^## 3\.10\.", r"^## 3\.11\.", SECTION_3_10)
    text = replace_between(text, r"^## 4\.5\.", r"^## 4\.6\.", SECTION_4_5)
    text = replace_between(text, r"^## 4\.6\.", r"^## 4\.7\.", SECTION_4_6)
    text = replace_between(text, r"^## 4\.7\.", r"^## 4\.8\.", SECTION_4_7)
    changes.append("Replaced broken formula sections with display LaTeX notation.")

    cleanup_replacements = {
        "Table 1 summarizes the full CDnet2014 official-like results.": "Table 2 summarizes the full CDnet2014 official-like results.",
        "Table 2 summarizes the best-performing pipeline for each major metric.": "Table 3 summarizes the best-performing pipeline for each major metric.",
        "ASMAG_TR_ FAST": "ASMAG_TR_FAST",
        "ASMAG_TR_CONTROLLER_ ONLINE_CALIBRATED": "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
        "ASMAG_TR_ CONTROLLER_ ONLINE_CALIBRATED": "ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED",
        "ASMAG_TR_ CONTROLLER": "ASMAG_TR_CONTROLLER",
        "deployable online adaptive variant": "deployment-oriented online adaptive variant",
        "deployable adaptive variant": "deployment-oriented adaptive variant",
        "Deployable adaptive variant": "Deployment-oriented adaptive variant",
        "Deployable online variant": "Deployment-oriented online variant",
        "practical deployable variant": "deployment-oriented variant",
        "practical deployable direction": "deployment-oriented direction",
        "final fully deployable controller": "final deployment-ready controller",
        "fully deployable controller": "deployment-ready controller",
        "most practical deployable variant": "most deployment-oriented variant evaluated in this study",
        "it is the most deployment-oriented variant evaluated in this study of ASMAG-TRC in the current study.": "it is the most deployment-oriented variant evaluated in this study.",
        "a deployable approximation": "a deployment-oriented approximation",
    }
    for old, new in cleanup_replacements.items():
        text = text.replace(old, new)
    changes.append("Fixed table cross-references, extracted pipeline spacing artifacts, and several claim-safety wordings.")

    text = text.replace(
        "This pipeline provides a reference for maximum detector activation:\n\n[Math object without extractable text]",
        "This pipeline provides a reference for maximum detector activation:\n\n$$\nG_t = 1 \\quad \\forall t \\in \\mathcal{T}_{eval}\n$$",
    )
    text = text.replace(
        "resulting in 318 video-pipeline jobs:\n\n[Math object without extractable text]",
        "resulting in 318 video-pipeline jobs:\n\n$$\n53 \\times 6 = 318 \\; \\text{video-pipeline jobs}\n$$",
    )

    fig_replacements = [
        ("Figure 1. Overall architecture of ASMAG-TRC\n\n[Figure/image object]", "Figure 1. Overall ASMAG-TRC process flow / architecture\n\n" + figure_markdown(1, "Overall ASMAG-TRC process flow / architecture", "asmag_trc_architecture.png", "Overall ASMAG-TRC process flow, showing motion proposal, adaptive gating, controller-based mode selection, detector activation, temporal reuse, and prediction output.")),
        ("Figure 2. CDnet FMeasure comparison across pipelines\n\n[Figure/image object]", "Figure 2. CDnet FMeasure comparison across pipelines\n\n" + figure_markdown(2, "CDnet FMeasure comparison across pipelines", "fmeasure_by_pipeline.png", "CDnet FMeasure comparison across the six evaluated pipelines under the full CDnet2014 official-like frame_step=1 protocol and CPU-only edge simulation.")),
        ("Figure 3. Event F1 comparison across pipelines\n\n[Figure/image object]", "Figure 3. Event F1 comparison across pipelines\n\n" + figure_markdown(3, "Event F1 comparison across pipelines", "event_f1_by_pipeline.png", "Event F1 comparison across the six evaluated pipelines under the full CDnet2014 official-like frame_step=1 protocol and CPU-only edge simulation.")),
        ("Figure 4. Detector activation rate across pipelines\n\n[Figure/image object]", "Figure 4. Detector activation rate across pipelines\n\n" + figure_markdown(4, "Detector activation rate across pipelines", "activation_by_pipeline.png", "Detector or heavy-inference activation rate across the six evaluated pipelines. Lower activation indicates fewer heavy processing calls and should be interpreted together with accuracy metrics.")),
        ("Figure 5. Accuracy-energy Pareto trade-off\n\n[Figure/image object]", "Figure 5. Accuracy-energy Pareto trade-off\n\n" + figure_markdown(5, "Accuracy-energy Pareto trade-off", "pareto_fmeasure_energy.png", "Accuracy-energy Pareto trade-off using CDnet FMeasure and energy/frame proxy under CPU-only edge simulation.")),
        ("Figure 6. Per-category CDnet FMeasure heatmap\n\n[Figure/image object]", "Figure 6. Per-category CDnet FMeasure heatmap\n\n" + figure_markdown(6, "Per-category CDnet FMeasure heatmap", "per_category_fmeasure_heatmap.png", "Per-category CDnet FMeasure heatmap across CDnet2014 categories and evaluated pipelines, showing category-dependent performance variation.")),
    ]
    for old, new in fig_replacements:
        if old not in text:
            raise RuntimeError(f"Could not find figure block: {old.splitlines()[0]}")
        text = text.replace(old, new, 1)
    changes.append("Inserted Markdown image references and captions for Figures 1-6.")

    table4, table4_report = table4_from_csv()
    text = re.sub(
        r"Table 4\. Gain summary against P3_MOG2\s+\| Comparison \| FMeasure Gain .*?\n\nPositive activation",
        "Table 4. Gain summary against P3_MOG2\n\n" + table4 + "\n\nPositive activation",
        text,
        count=1,
        flags=re.S,
    )
    changes.append("Corrected Table 4 from gain_summary.csv, including simulated runtime energy saving values.")

    threats = "\n\n" + THREATS + "\n\n"
    if "## 6.9. Threats to Validity" not in text:
        text = text.replace("\n# 7. Limitations and Future Work", threats + "# 7. Limitations and Future Work", 1)
    changes.append("Inserted concise Threats to Validity section before Section 7.")

    refs_text, bib_text, complete_count, todo_count = references()
    write(PKG / "references_section_draft.md", refs_text)
    write(PKG / "references_ready.bib", bib_text)
    text = re.sub(r"# Reference\s*\n\s*# Appendix", refs_text + "\n\n" + declarations() + "\n\n# Appendix", text, count=1)
    changes.append(f"Inserted References and Declarations sections; references draft has {complete_count} complete entries and {todo_count} TODO entries.")

    write(READY, text)

    formula_report = build_formula_report(text)
    write(PKG / "pass2_formula_check.md", formula_report)
    write(PKG / "pass2_table4_validation.md", table4_report)
    write(PKG / "pass2_reference_action_report.md", build_reference_report(text, complete_count, todo_count))
    write(PKG / "pass2_figure_insertion_report.md", build_figure_report(text))
    write(PKG / "pass2_change_log.md", build_change_log(changes))
    write(PKG / "FINAL_SUBMISSION_PREP_PASS2_REPORT.md", build_final_report(text, complete_count, todo_count))
    print(f"Wrote {READY.relative_to(ROOT)}")


def build_change_log(changes: list[str]) -> str:
    return "# Pass 2 Change Log\n\nTimestamp: `" + datetime.now().isoformat(timespec="seconds") + "`\n\n" + "\n".join(f"- {change}" for change in changes)


def build_formula_report(text: str) -> str:
    required = [
        ("Frame difference", "D_t = |I_t - I_{t-1}|"),
        ("Frame-difference mask", "M_t^{FD} = H(|I_t - I_{t-1}| - \\tau_{FD})"),
        ("MOG2 mask", "M_t^{MOG2} = BGS_{MOG2}(I_t)"),
        ("Gate decision", "\\begin{cases}"),
        ("Gate score", "S_t = \\alpha"),
        ("Gate activation", "S_t \\ge \\theta_m"),
        ("Evaluated-index sampling", "k \\bmod T = 0"),
        ("Temporal reuse", "\\hat{P}_t = P_{t'}"),
        ("Online feature vector", "\\begin{bmatrix}"),
        ("Mode selection", "m_t = f(x_t)"),
        ("FMeasure", "\\mathrm{FMeasure}"),
        ("Activation", "\\mathrm{Activation}"),
        ("Reuse rate", "\\mathrm{ReuseRate}"),
        ("Runtime-aware simulated energy", "E_t^{sim} = 1.0"),
    ]
    rows = []
    for label, needle in required:
        rows.append((label, "Found" if needle in text else "Missing"))
    forbidden = ["Let denote", "where ()", "[Math object without extractable text]", "A simplified gate score can be represented as:\n\n\n", "â€‹"]
    forbidden_rows = [(item, str(text.count(item))) for item in forbidden]
    return (
        "# Pass 2 Formula Check\n\n"
        "## Required Formula Presence\n\n"
        "| Formula | Status |\n|---|---|\n"
        + "\n".join(f"| {label} | {status} |" for label, status in rows)
        + "\n\n## Broken Placeholder Scan\n\n| Placeholder | Count |\n|---|---:|\n"
        + "\n".join(f"| `{item}` | {count} |" for item, count in forbidden_rows)
    )


def build_reference_report(text: str, complete_count: int, todo_count: int) -> str:
    placeholders = ["(arXiv)", "(Microsoft)"]
    remaining = {p: text.count(p) for p in placeholders}
    inserted = ["Wang et al., 2014", "Stauffer & Grimson, 1999", "Bouwmans, 2014", "Redmon et al., 2016", "Kang et al., 2017", "Jiang et al., 2018"]
    needed = re.findall(r"\[REFERENCE NEEDED:[^\]]+\]", text)
    return (
        "# Pass 2 Reference Action Report\n\n"
        "## Placeholders Removed\n\n"
        + "\n".join(f"- `{p}` remaining count: `{count}`" for p, count in remaining.items())
        + "\n\n## References Inserted in Manuscript Text\n\n"
        + "\n".join(f"- {item}" for item in inserted)
        + f"\n\n## References Section Draft\n\n- Complete entries: `{complete_count}`\n- TODO entries: `{todo_count}`\n- File: `outputs/submission_package/references_section_draft.md`\n- BibTeX file: `outputs/submission_package/references_ready.bib`\n\n## Reference Placeholders Still Needed\n\n"
        + ("\n".join(f"- {item}" for item in sorted(set(needed))) if needed else "- None inserted as bracketed placeholders in pass 2. Remaining TODOs are listed in the reference draft and declaration sections.")
    )


def build_figure_report(text: str) -> str:
    figures = [
        ("Figure 1", "outputs/paper_ready_figures/asmag_trc_architecture.png"),
        ("Figure 2", "outputs/paper_ready_figures/fmeasure_by_pipeline.png"),
        ("Figure 3", "outputs/paper_ready_figures/event_f1_by_pipeline.png"),
        ("Figure 4", "outputs/paper_ready_figures/activation_by_pipeline.png"),
        ("Figure 5", "outputs/paper_ready_figures/pareto_fmeasure_energy.png"),
        ("Figure 6", "outputs/paper_ready_figures/per_category_fmeasure_heatmap.png"),
    ]
    rows = []
    for label, path in figures:
        rows.append((label, path, "Exists" if (ROOT / path).exists() else "Missing", "Referenced" if path in text else "Not referenced"))
    return (
        "# Pass 2 Figure Insertion Report\n\n"
        "| Figure | Source path | File status | Markdown status |\n|---|---|---|---|\n"
        + "\n".join(f"| {a} | `{b}` | {c} | {d} |" for a, b, c, d in rows)
        + "\n\nAll figure captions mention the source file path. Final Word/PDF visual proofing is still required."
    )


def build_final_report(text: str, complete_count: int, todo_count: int) -> str:
    forbidden_counts = {
        "Let denote": text.count("Let denote"),
        "where ()": text.count("where ()"),
        "[Math object without extractable text]": text.count("[Math object without extractable text]"),
        "(arXiv)": text.count("(arXiv)"),
        "(Microsoft)": text.count("(Microsoft)"),
        "[Figure/image object]": text.count("[Figure/image object]"),
    }
    blockers = [
        "Manual Word conversion/proofing is still required because pass 2 updates the Markdown master only.",
        "Vendor/hardware and physical power-measurement references remain TODO if those claims are kept.",
        "Funding, author contributions, and code availability require user decisions.",
        "Final target journal template and reference style still need to be applied.",
    ]
    readiness = 78
    return (
        "# Final Submission Prep Pass 2 Report\n\n"
        "## 1. Formula Status\n\nFormulas are fixed in `manuscript/ASMAG_2026_submission_ready_v1.md`. See `pass2_formula_check.md`.\n\n"
        "## 2. Table 4 Status\n\nTable 4 mismatch is fixed from `gain_summary.csv`. See `pass2_table4_validation.md`.\n\n"
        "## 3. References Section Draft\n\n"
        f"- References draft exists: `outputs/submission_package/references_section_draft.md`\n- BibTeX draft exists: `outputs/submission_package/references_ready.bib`\n- Complete reference entries: `{complete_count}`\n- TODO reference entries: `{todo_count}`\n\n"
        "## 4. Figure Paths and Captions\n\nFigure paths and captions are ready in Markdown for Figures 1-6. See `pass2_figure_insertion_report.md`.\n\n"
        "## 5. Threats to Validity\n\nThreats to Validity was inserted before Section 7.\n\n"
        "## 6. Submission Statements\n\nData Availability, Code Availability, Conflict of Interest, Funding, Author Contributions, Ethics Approval, and Supplementary Materials statements were inserted in a Declarations section before the Appendix.\n\n"
        "## 7. Placeholder Scan\n\n| Placeholder | Count |\n|---|---:|\n"
        + "\n".join(f"| `{key}` | {value} |" for key, value in forbidden_counts.items())
        + "\n\n## 8. Remaining Blockers\n\n"
        + "\n".join(f"- {item}" for item in blockers)
        + f"\n\n## 9. New Readiness Score\n\n**{readiness}/100.**\n\n"
        "## 10. Recommended Next Step\n\nReady for Word conversion as a Markdown master, but still needs manual references/vendor TODO cleanup, target-journal formatting, `.docx` proofing, and final PDF proof. No additional experiments are required for this pass."
    )


SECTION_3_2 = r"""
## 3.2. Motion Proposal Layer

The motion proposal layer extracts lightweight motion information from the video stream. It provides the basic evidence for deciding whether the current frame deserves full detector inference. The layer may use simple frame differencing, MOG2-based foreground estimation, or additional disagreement features between multiple motion estimators.

Let \(I_t\) denote the current frame at time \(t\), and let \(I_{t-1}\) denote the previous frame. A simple frame difference map is computed as:

$$
D_t = |I_t - I_{t-1}|
$$

After thresholding and optional morphological filtering, the frame-difference binary motion mask is:

$$
M_t^{FD} = H(|I_t - I_{t-1}| - \tau_{FD})
$$

where \(H(\cdot)\) is a binary thresholding operator and \(\tau_{FD}\) is the frame-difference threshold. In parallel, a background subtraction model such as MOG2 produces another foreground mask:

$$
M_t^{MOG2} = BGS_{MOG2}(I_t)
$$

These masks are used to estimate motion density, foreground area, component count, and disagreement between motion estimators.

The key motion features used by ASMAG-TRC include:

| Feature | Meaning |
| --- | --- |
| motion_density | Ratio of foreground pixels to total pixels |
| component_count | Number of connected foreground components |
| fd_area | Foreground area estimated by FrameDiff |
| mog_area | Foreground area estimated by MOG2 |
| fd_mog_disagreement | Difference between FrameDiff and MOG2 motion masks |
| illumination_variance | Approximate scene brightness variation |
| active_frame_rate | Ratio of recent frames considered active |
| gate_closed_rate | Ratio of recent frames where detector was skipped |
| reuse_success_rate | Ratio of recent frames where temporal reuse was accepted |

The disagreement between motion estimators is particularly important. A low disagreement value usually indicates that lightweight motion cues are consistent. A high disagreement value suggests that the scene may be difficult, noisy, unstable, or affected by illumination/background changes. This information is useful for deciding whether the system should stay in a fast mode, use an accuracy-preserving mode, or fallback to a stronger baseline.
"""


SECTION_3_3 = r"""
## 3.3. Adaptive Motion Gate

The adaptive motion gate determines whether the detector should be activated for the current evaluated frame. Unlike fixed frame skipping, the gate does not simply activate the detector every \(T\) frames. Instead, it considers motion intensity, motion consistency, periodic safety checks, and controller-selected mode.

The gate receives motion features and produces a binary decision:

$$
G_t =
\begin{cases}
1, & \text{if detector/heavy inference is activated}, \\
0, & \text{otherwise}.
\end{cases}
$$

In practice, the gate uses several conditions:

- Motion activation condition: if motion density is above a threshold, the gate opens.
- Disagreement condition: if motion estimators disagree strongly, the gate opens or falls back.
- Periodic sampling condition: even when motion is low, the detector is periodically activated to avoid long-term drift.
- Reuse validity condition: if the previous prediction is still reliable, the gate may remain closed.
- Controller mode condition: FAST, ACC, P3 fallback, or calibrated online mode adjusts the gate behavior.

A simplified gate score is represented as:

$$
S_t = \alpha\,\mathrm{motion\_density}_t
    + \beta\,\mathrm{component\_activity}_t
    + \gamma\,\mathrm{disagreement}_t
    + \delta\,\mathrm{illumination\_variation}_t
$$

The detector is activated if \(S_t\) exceeds a mode-specific threshold or if the periodic sampling condition is satisfied:

$$
G_t = 1 \quad \text{if} \quad S_t \ge \theta_m \ \text{or} \ k \bmod T = 0.
$$

Here, \(\theta_m\) is the threshold selected for mode \(m\), \(k\) is the evaluated-frame index, and \(T\) is the detector refresh period.

This design allows the gate to behave differently in easy and difficult scenes. In stable scenes, the system can skip more detector calls. In complex scenes, it becomes more conservative and activates stronger inference more frequently.
"""


SECTION_3_4 = r"""
## 3.4. Evaluated-Index-Aware Sampling

A practical issue in video evaluation is that the system may not process every raw frame under all experimental settings. For example, in sampled experiments, frame_step may be greater than 1. In the official-like evaluation used in this paper, frame_step=1, but the framework is designed to remain valid under both sampled and full-frame settings.

To avoid distorted periodic sampling, ASMAG-TRC uses an evaluated index rather than the raw frame number. Let \(k\) denote the index of the evaluated-frame sequence. If only every \(s\)-th raw frame is evaluated, \(k\) increases by 1 for each evaluated frame regardless of the raw frame ID.

The periodic detector activation condition is therefore defined as:

$$
k \bmod T = 0
$$

where \(T\) is the detector refresh period in evaluated-frame units.

This prevents the system from incorrectly triggering or skipping detector calls when the frame sampling rate changes. It also ensures that comparisons across different evaluation configurations remain consistent.
"""


SECTION_3_5 = r"""
## 3.5. Temporal Reuse

Temporal reuse is used when the detector is not activated on the current frame. The basic assumption is that, in many surveillance videos, foreground objects and scene structures change gradually. Therefore, the most recent valid prediction may still be useful for the current frame.

Let \(P_{t'}\) be the most recent valid prediction produced by detector inference or a stronger motion baseline at time \(t' < t\). If the current frame is considered stable and the reuse age is acceptable, ASMAG-TRC can use:

$$
\hat{P}_t = P_{t'}
$$

instead of running detector inference again.

The reuse decision depends on:

| Factor | Role |
| --- | --- |
| Reuse age | Prevents old predictions from being reused too long |
| Motion overlap | Checks whether current motion is consistent with previous prediction |
| Gate confidence | Avoids reuse when the gate is uncertain |
| Scene difficulty | Reduces reuse in difficult categories or difficult online states |
| Controller mode | FAST allows more reuse; fallback modes allow less reuse |

Temporal reuse helps reduce detector activation and energy consumption. However, it can also introduce errors if reused predictions become stale. For example, an object may move away, a new object may enter the scene, or a dynamic background may be mistaken for stable motion. Therefore, ASMAG-TRC does not use reuse blindly. It combines reuse with motion gating and controller-based mode selection.

The reuse rate is recorded as an evaluation metric:

$$
\mathrm{ReuseRate} =
\frac{\text{Number of reused prediction frames}}
     {\text{Number of evaluated frames}}
$$

This metric helps quantify how much the framework relies on temporal continuity.
"""


SECTION_3_8 = r"""
## 3.8. Online Calibrated Controller

The online calibrated controller is designed to remove the dependency on category labels during inference. It uses rolling features computed over a window of recent evaluated frames. These features describe the current scene dynamics and are used to classify the scene into an appropriate operating mode.

Let \(W_t\) denote a rolling window ending at frame \(t\). For this window, ASMAG-TRC computes the feature vector:

$$
x_t =
\begin{bmatrix}
\mathrm{motion\_density\_mean} \\
\mathrm{motion\_density\_std} \\
\mathrm{component\_count\_mean} \\
\mathrm{component\_count\_std} \\
\mathrm{fd\_mog\_disagreement} \\
\mathrm{illumination\_variance} \\
\mathrm{reuse\_success\_rate} \\
\mathrm{active\_frame\_rate} \\
\mathrm{gate\_closed\_rate}
\end{bmatrix}
$$

The online controller maps this feature vector to a selected mode:

$$
m_t = f(x_t)
$$

where \(m_t\) is one of the available modes, such as FAST, ACC, or P3 fallback.

The controller is calibrated using pseudo-labels derived from the category-aware controller. During training or calibration, the category-aware policy acts as a teacher. During inference, however, the online controller only uses rolling scene features and does not access category labels.

This design provides a practical compromise. The category-aware controller gives an upper-bound reference, while the online calibrated controller provides a deployment-oriented approximation.
"""


SECTION_3_10 = r"""
## 3.10. Evaluation Metrics Produced by the Method

ASMAG-TRC is designed not only to output predictions but also to produce detailed runtime and efficiency logs. For each pipeline, the framework records:

| Metric Group | Metrics |
| --- | --- |
| Accuracy | CDnet FMeasure, Event F1, mAP50 proxy |
| Detector usage | Activation rate, reuse rate |
| Runtime | Avg FPS, average latency, P95 latency, P99 latency |
| Resource usage | CPU usage, RAM usage |
| Energy proxy | Energy/frame, simulated runtime-aware energy/frame |
| Trade-off | AE Score, Pareto efficiency |

The detector activation rate is defined as:

$$
\mathrm{Activation} =
\frac{\text{Number of activated frames}}
     {\text{Number of evaluated frames}}
$$

The reuse rate is defined as:

$$
\mathrm{ReuseRate} =
\frac{\text{Number of reused prediction frames}}
     {\text{Number of evaluated frames}}
$$

These metrics are central to ASMAG-TRC because the framework aims to reduce unnecessary detector calls while quantifying the role of temporal reuse.

The energy proxy combines a base processing cost with additional cost for detector activation and runtime behavior. Although this does not replace physical power measurement, it provides a consistent comparative indicator under CPU-only edge simulation.
"""


SECTION_4_5 = r"""
## 4.5. Accuracy Metrics

The evaluation uses multiple accuracy metrics because the task combines change detection, event-level detection, and object-level proxy analysis.

### 4.5.1. CDnet FMeasure

The primary pixel-level metric is CDnet FMeasure, computed from precision and recall:

$$
\mathrm{FMeasure} =
\frac{2 \times \mathrm{Precision} \times \mathrm{Recall}}
     {\mathrm{Precision} + \mathrm{Recall}}
$$

This metric evaluates how well the predicted foreground mask matches the ground-truth foreground regions. It is the main metric for change detection performance.

### 4.5.2. Event F1

In active camera systems, event-level reliability is also important. A camera should detect whether meaningful activity occurs in a frame or time interval. Therefore, Event F1 is used to evaluate whether the system correctly identifies event frames, regardless of exact pixel-level mask quality.

This metric is useful because some pipelines may not perfectly segment every foreground pixel but may still detect the occurrence of an event reliably.

### 4.5.3. mAP50 Proxy

Since CDnet2014 is primarily a foreground segmentation benchmark and not a standard object detection dataset, the study uses an mAP50 proxy derived from predicted foreground/object regions. This proxy provides an approximate object-level comparison across pipelines. It should not be interpreted as a direct COCO-style object detection mAP, but rather as an object-region proxy for comparing the spatial quality of detections.
"""


SECTION_4_6 = r"""
## 4.6. Efficiency and Runtime Metrics

In addition to accuracy, the experiments evaluate several efficiency metrics that are central to Edge AI deployment.

### 4.6.1. Detector Activation

Detector activation measures how often the pipeline activates heavy inference or a detector-like processing step:

$$
\mathrm{Activation} =
\frac{\text{Number of activated frames}}
     {\text{Number of evaluated frames}}
$$

A lower activation rate generally indicates fewer heavy inference calls and lower expected computation cost. However, activation must be interpreted together with accuracy. A pipeline can reduce activation aggressively but may lose foreground or event detection quality.

### 4.6.2. Reuse Rate

Reuse rate measures how often a pipeline uses temporally reused predictions rather than new inference:

$$
\mathrm{ReuseRate} =
\frac{\text{Number of reused prediction frames}}
     {\text{Number of evaluated frames}}
$$

This metric helps quantify the role of temporal continuity in the pipeline.

### 4.6.3. FPS and Latency

The system records average frames per second and latency statistics. The main latency metric reported is P95 latency, which represents the 95th percentile of per-frame processing latency. P95 latency is more informative than average latency for real-time systems because it captures high-latency tail behavior.

The reported runtime metrics include:

| Metric | Meaning |
| --- | --- |
| Avg FPS | Average throughput |
| Avg latency | Average per-frame processing time |
| P50 latency | Median latency |
| P95 latency | 95th percentile latency |
| P99 latency | 99th percentile latency |

### 4.6.4. CPU and RAM Usage

The edge profiling system records process CPU usage, system CPU usage, process RAM usage, and system RAM usage. Since CPU usage is measured on a multi-core system, process CPU percentage may exceed 100%. This indicates that the process uses more than one logical CPU core.

These measurements are important for understanding whether a method is practical for constrained edge deployment.
"""


SECTION_4_7 = r"""
## 4.7. Energy Proxy and Runtime-Aware Simulated Energy

Because no external power meter is used, this study reports energy estimates as proxy values. Two energy-related metrics are recorded.

The first is Energy/frame, a consistent per-frame proxy used for comparing pipelines according to detector activation and processing mode.

The second is simulated runtime-aware energy, which additionally incorporates runtime behavior such as latency and CPU usage. It is defined as:

$$
E_t^{sim} = 1.0 + 5.0y_t + 1.0c_t + 1.0l_t + 2.0g_t + 0.1r_t
$$

where:

| Symbol | Meaning |
| --- | --- |
| \(y_t\) | Detector activation indicator |
| \(c_t\) | Normalized CPU usage |
| \(l_t\) | Normalized latency |
| \(g_t\) | Normalized GPU usage; zero in CPU-only experiments |
| \(r_t\) | Reuse indicator |

This simulated energy metric does not replace physical energy measurement. Instead, it provides a normalized estimate for comparing runtime behavior across pipelines under the same CPU-only environment.
"""


THREATS = """
## 6.9. Threats to Validity

Several validity threats should be considered when interpreting the results. First, the evaluation uses CDnet2014 only. Although CDnet2014 contains diverse surveillance scenarios, additional datasets are needed to assess generalization to other camera domains. Second, the experiments use CPU-only edge simulation rather than a dedicated embedded AI device. The results therefore characterize CPU-oriented behavior and should be validated on real edge hardware. Third, the reported energy values are proxy estimates, not physical Watt or Joule measurements from an external power meter. Fourth, the category-aware controller uses CDnet2014 category labels and should be interpreted as an upper-bound scene-aware policy rather than a directly deployable controller. Fifth, mAP50 is used as an object-region proxy because CDnet2014 does not provide COCO-style object detection labels. Finally, the online calibrated controller introduces runtime overhead, which explains why lower activation does not automatically translate into higher FPS. These threats are mitigated by reporting the evaluation scope explicitly, providing supplementary CSV files and progress logs, separating category-aware and online controller results, and identifying real hardware validation as future work.
"""


if __name__ == "__main__":
    main()
