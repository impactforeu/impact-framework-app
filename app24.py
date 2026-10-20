import streamlit as st
import sqlite3
import os
import pandas as pd
import io

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('impact_logbook.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reflections (
            username TEXT,
            module TEXT,
            question TEXT,
            answer TEXT,
            UNIQUE(username, module, question)
        )
    ''')
    conn.commit()
    return conn

def save_answer(conn, username, module, question, answer):
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO reflections (username, module, question, answer)
        VALUES (?, ?, ?, ?)
    ''', (username, module, question, answer))
    conn.commit()

def load_answer(conn, username, module, question):
    c = conn.cursor()
    c.execute('SELECT answer FROM reflections WHERE username=? AND module=? AND question=?', 
              (username, module, question))
    result = c.fetchone()
    return result[0] if result else ""

def get_progress(conn, username):
    """Calculates progress based on how many core modules have saved answers."""
    c = conn.cursor()
    c.execute('SELECT DISTINCT module FROM reflections WHERE username=? AND answer != ""', (username,))
    rows = c.fetchall()
    core_modules_started = [row[0] for row in rows if row[0].startswith('Module ')]
    
    total_core_modules = 7.0
    progress_fraction = len(core_modules_started) / total_core_modules
    return min(progress_fraction, 1.0) 

# --- 2. APP CONFIGURATION & LOGIN ---
st.set_page_config(page_title="IMP>ACT Framework", page_icon="🌱", layout="wide")

# --- CUSTOM CSS TO MATCH DASHBOARD THEME ---
st.markdown(
    """
    <style>
    /* 1. Import Montserrat Font */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&display=swap');

    /* 2. Global Font and Text Color */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
        color: #2b3338 !important;
    }

    /* 3. Main App Background & Top Header */
    [data-testid="stAppViewContainer"] {
        background-color: #f3f3f3 !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important; /* Removes the ugly white bar on top */
    }

    /* 4. Headers in Slate Blue */
    h1, h2, h3, h4, h5, h6 {
        color: #4e5a62 !important;
        font-weight: 700 !important;
    }

    /* 5. Style Expanders to look like Dashboard Cards */
    [data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #d8dde0;
        border-radius: 8px;
        box-shadow: none;
    }
    [data-testid="stExpander"] summary {
        color: #4e5a62;
        font-weight: 700;
        border-bottom: 2px solid transparent;
    }
    [data-testid="stExpander"] summary:hover {
        border-bottom: 2px solid #a7ce45;
    }

    /* 6. Style the Buttons */
    .stButton > button {
        background-color: #a7ce45 !important;
        color: #2b3338 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    .stButton > button:hover {
        background-color: #92b83b !important;
        color: #ffffff !important;
    }

    /* 7. Sidebar Navigation Adjustments */
    [data-testid="stSidebar"] {
        background-color: #e8ecef !important; /* Soft, darker grey instead of harsh white */
        border-right: 3px solid #a7ce45;
    }
    [data-testid="stSidebar"] .stRadio p {
        font-size: 16px !important;
        font-weight: 400 !important; /* Removed the overwhelming bold text */
        color: #4e5a62 !important;
    }
    
    /* 8. Text Inputs and Text Areas (Make them white for contrast) */
    .stTextInput div[data-baseweb="input"], 
    .stTextArea div[data-baseweb="textarea"],
    .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 2px solid #4e5a62 !important; /* Bold Slate Blue border */
        border-radius: 6px !important;
    }

    /* Make the border glow IMP>ACT Green when typing */
    .stTextInput div[data-baseweb="input"]:focus-within, 
    .stTextArea div[data-baseweb="textarea"]:focus-within {
        border-color: #a7ce45 !important; 
    }

    /* 9. Info/Success boxes */
    [data-testid="stAlert"] {
        border-radius: 8px;
    }
    
    /* 10. Reduce excessive top padding */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

conn = init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''

# State variable for the persistent success message
if 'save_success' not in st.session_state:
    st.session_state['save_success'] = None

if not st.session_state['logged_in']:
    st.title("🌱 Welcome to the IMP>ACT Assessment Framework")
    st.markdown("Please log in with an email address of your choice. Use this email address for future logins.")
    
    username_input = st.text_input("Enter your unique Username or Email:")
    if st.button("Log In"):
        if username_input:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username_input
            st.rerun()
        else:
            st.warning("Please enter a username.")

# --- 3. THE MODULAR FRAMEWORK (LOGGED IN) ---
else:
    user = st.session_state['username']
    
    st.sidebar.title(f"👤 User: {user}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()
        
    st.sidebar.markdown("---")
    
    progress_val = get_progress(conn, user)
    st.sidebar.progress(progress_val, text=f"Framework Progress: {int(progress_val * 100)}%")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Modules")
    
    module = st.sidebar.radio("Navigate your pathway:", 
                              ["Welcome & Navigation",
                               "1. Introduction to the IMP>ACT Framework",
                               "2. Your Organisation",
                               "3. Goal Setting",
                               "4. Backing of Claims",
                               "5. Indicators and instruments",
                               "6. Interpreting data and information",
                               "7. Action planning",
                               "Summary & Export",
                               "Background reading"])
    st.sidebar.markdown("---")
    # --- QUICK GLOSSARY IN SIDEBAR ---
    with st.sidebar.expander("📖 Quick Glossary"):
        st.markdown("**SCCE:** Sustainability and Climate Change Education.")
        st.markdown("**AC:** Action Competence.")
        st.markdown("**AO:** Action Orientation.")
        st.markdown("**Action-Oriented Approach:** Teaching and learning approaches that foster learners’ action competence by empowering them to make democratic decisions, act autonomously, and take responsibility.")
        st.markdown("**Assessment Model:** The foundation defining what to evaluate (conceptual basis) and the tools to do so (measurement instruments, indicators).")
        st.markdown("**Assessment Methodology:** The step-by-step process of designing and performing the assessment to meet specific organisational needs.")
        st.markdown("**SCCE Policy:** A set of guidelines or rules that aims to improve the quality of SCCE.")
        st.markdown("**SCCE Practice:** A concrete activity (or a set of activities) that aims to foster the development of action competence as part of learning.")
        st.markdown("**Assessment:** The process of gathering information about the outcomes (impacts) of SCCE policies or practices.")
        st.markdown("**Evaluation:** A process for determining whether programs have met expected objectives and/or the extent to which changes in outcomes can be attributed to the program.")
        st.markdown("**Monitoring:** The ongoing, systematic collection and analysis of data as SCCE policies or practices progress across time.")
        st.markdown("**Measurement Instruments:** Practical tools (like surveys or rubrics) used to collect raw data.")
        st.markdown("**Indicators:** Specific signposts or metrics that translate collected data into a clear picture of progress.")
        st.markdown("**User-validity:** The extent to which an assessment framework or tool is useful, meaningful, and appropriate for its intended users.")
        st.markdown("**Program:** A set of interconnected activities aiming to achieve one or more common goals.")
        st.markdown("**SP / AP:** Societal Partner / Academic Partner.")
    st.sidebar.markdown("---")

    # --- MODULE 0: WELCOME ---
    if module == "Welcome & Navigation":
        st.title("👋 Welcome to the IMP>ACT Assessment Framework")
        
        st.markdown("""
        ### What is this framework?
        The IMP>ACT assessment framework is designed to guide users in developing an assessment methodology based on the goals, claims, and possibilities of their organisation in assessing the outcomes of sustainability and climate change education. Rather than being a purely theoretical guide, the framework is a practical instrument that helps users formulate and respond to key questions that shape their own assessment methodology.

        With a wide range of potential applications, the framework is designed to be flexible and adaptable to the specific needs of its users. Examples of potential users include:
        * A NGOs supporting teachers in integrating SCCE into their teaching, for instance, through professional development.
        * An educational department of a local municipality that is implementing SCCE workshops in primary schools.
        * A national scouting organisation helping youth leaders address climate change in informal learning settings.
        * A regional authority that is developing policies to foster public support for climate action through educational initiatives.
        * An association of teacher educators designing programs to build SCCE-related competencies.
        * A museum curating a temporary exhibition on climate change.
        * An organisation conducting large-scale educational assessments, seeking valid and meaningful data on SCCE learning outcomes.
        * …

        These diverse users, active in SCCE policy and practice, have varying needs and expectations regarding impact assessment. Some may wish to evaluate a flagship project, others may aim to monitor citizens’ action competence over time, and many other use cases are possible. 
        """)
 
        st.info("""
        **💡Note:** 
        The framework does not aim to provide you with a clear-cut impact assessment plan. Instead, it provides you with a set of steps to follow, allowing your organisation to consider its organisational goals, claims, needs, and possibilities when assessing SCCE.
        """)

        st.video("https://www.youtube.com/watch?v=AF2PkoHDpak")
        st.markdown("Check out the [IMP>ACT Website](https://impactforaction.eu/) for more information!")       
        st.markdown("---")
        
        st.markdown("""
        ### 🧭 How to navigate the framework
        
        * **The Sidebar Menu:** Use the navigation panel on the left to move between modules. We recommend starting at Module 1 and working your way down, but you can jump back and forth anytime.
        * **Expandable Theory:** To keep your workspace clean, the heavy theoretical background is hidden inside clickable drop-down boxes (labeled with a 📚). Click them to read the theory before answering the questions.
        * **Reflection Questions:** Throughout the modules, you will find interactive questions designed to guide your organisation through the data use cycle. This logbook is not a simple "fill-in-the-blanks" form; it is a reflective tool meant to be completed thoughtfully, ideally in discussion with your team, to shape an assessment that fits your specific context.
        * **The Glossary:** On the bottom of the navigation panel you'll find a 'Quick Glossary'. This Glossary contains some important definitions that are used in the framework. If you are unsure about the meaning of something, you'll probably find an explanation there!
        * **Saving Your Progress:** At the bottom of each module, you will find a green **Save** button. *You must click this button before moving to the next module to store your reflections!*
        """)
        
        st.info("""
        **📋 The Logbook:** 
        Every time you save an answer, it is automatically sent to your **Summary & Export** dashboard (the penultimate module in the menu). Once you finish the modules, you can visit the Summary page to view your complete, customized Evaluation Design and download it as a text Word or PDF file to share it with your team or organisation!
        """)


        
        # --- NEW CALL TO ACTION ---
        st.markdown("---")
        st.success("""
        ✨ **Ready to discover what the IMP>ACT framework has to offer?** 
        
        Head over to the navigation menu on the left and click on **1. Introduction to the IMP>ACT Framework** to begin your journey!
        """)
        


    # --- MODULE 1 ---
    elif module == "1. Introduction to the IMP>ACT Framework":
        st.title("Module 1: Introduction to the IMP>ACT Framework")
        st.markdown("The IMP>ACT assessment framework is designed to guide users in developing an assessment methodology based on the goals, claims, and possibilities of their organisation in assessing the outcomes of <abbr title=\"Sustainability and Climate Change Education\">SCCE</abbr>.This section introduces the framework by describing its purpose, goals, core keywords, and how it is intended to be used.", unsafe_allow_html=True)
        
        # --- THEORY SECTION (Collapsible) ---
        st.subheader("📚 Core Concepts & Guidelines")
        
            
        with st.expander("Building blocks and key concepts"):
            st.markdown("""
            To clearly understand the framework, it is helpful to distinguish between its two main building blocks: the **Assessment Model** (the *what* and the *tools*) and the **Assessment Methodology** (the *how* and the *process*).
            """)
            
            # Pointing the app to the Images subfolder
            try:
                st.image("Images/figure 1.png", caption="Figure 1: Building blocks of the IMP>ACT framework", width=350)
            except FileNotFoundError:
                st.info("🖼️ [Image Placeholder: Make sure the building blocks image is saved as 'figure 1.png' inside the 'Images' folder.]")
                
            st.markdown("""
            ### 1. The Assessment Model
            The assessment model provides the foundation and the tools for your evaluation. As shown in Figure 1, it is built from the bottom up:
            *   **Conceptual basis:** This establishes the groundwork by defining the broad domains you want to evaluate (**areas for assessment**) and the specific ideas within those domains (**concepts**).
            *   **Measurement instruments:** To help you gather information about these concepts, the model provides practical tools (such as surveys, interviews, or observation rubrics). These tools are used to collect raw information, or **data**.
            *   **Indicators:** Finally, the model uses specific signposts or metrics that translate your collected data into a clear picture. These indicators show you your current state or track your progress regarding the conceptual basis.

            ### 2. The Assessment Methodology
            The assessment methodology is your step-by-step guide. It explains how to plan (**design**) and carry out an evaluation of your SCCE outcomes (**impact assessment**) so that it perfectly fits the specific needs of your organisation.
            
            This guide helps you clarify your goals, decide which data to collect, and determine how to turn that data into useful indicators. It also helps you understand what those indicators actually tell you—and what they *don't* tell you—about your organisational rules and guidelines (**policy**) or your actual educational activities (**practice**). 
            
            As visualised in the framework, the methodology relies on a continuous, healthy balance between three key elements:
            *   **Model application:** The practical use of the assessment model within your organisation.
            *   **Stakeholder roles:** The active involvement of relevant people (such as educators, learners, and community partners) in shaping and applying the model.
            *   **Feedback loops:** The continuous cycles of learning, reflection, and adaptation that emerge from using these insights to keep your activities, curricula, or policies up-to-date.
            
            ---
            
            ### Key Concepts & Glossary
            The IMP>ACT assessment framework functions as a lens through which you can reflect on and shape your own SCCE impact assessment practices. It is designed from a user-centred perspective, meaning *your* needs guide what will be assessed and inform your choices.
            
            *   **SCCE policy:** A set of guidelines or rules that aims to improve the quality of SCCE. This can be interpreted within organisations as well as within local, regional or national authorities.
            *   **SCCE practice:** A concrete activity (or a set of activities) that aims to foster the development of action competence as part of learning. This can be a single intervention (e.g., a single project implementation) or a broad program (e.g., activities of all eco-schools).
            *   **Assessment:** The process of gathering information about the outcomes (impacts) of SCCE policies or practices.
            *   **Evaluation:** A process for determining whether programs have met expected objectives and/or the extent to which changes in outcomes can be attributed to the program. This typically involves one evaluation moment.
            *   **Monitoring:** The ongoing, systematic collection and analysis of data as SCCE policies or practices progress across time.
            *   **User-validity:** The extent to which an assessment framework or tool is useful, meaningful, and appropriate for its intended users.
            *   **Program:** A set of interconnected activities aiming to achieve one or more common goals.
            
            ---
            💡 **Tip:** If you want to revisit these definitions while browsing the other modules, have a look at the **"📖 Quick Glossary"** at the bottom of the navigation menu on the left. All these definitions can be found there as well!
            """, unsafe_allow_html=True)
            
           
        with st.expander("Using the IMP>ACT framework (The Data Use Cycle)"):
            st.markdown("""
            Assessing the outcomes of your sustainability and climate change education (SCCE) is rarely an end in itself. Gathering information is usually just one step in a larger journey toward improving the quality of your educational activities.

            This journey is often described as a **data use circle of inquiry**—a continuous cycle of learning and improving based on information. While the exact process might vary, it typically involves four main phases:
            1. **Goal setting:** Deciding exactly what you want to achieve.
            2. **Collecting data:** Gathering new information or using information that is already available.
            3. **Interpretation and analysis:** Understanding what that information actually means.
            4. **Implementing action:** Taking steps to improve your practice based on what you learned.

            By moving through this cycle, you aren't just collecting raw numbers or feedback; you are giving meaning to them. You use this information systematically to build new knowledge, figure out what works, and decide what actions are needed to improve your SCCE.
            """)
            
            try:
                st.image("Images/figure 2.png", caption="Figure 2: Data use circle of inquiry, modelled on Hoefkens et al., (2024)", width=650)
            except FileNotFoundError:
                st.info("🖼️ [Image Placeholder: Make sure the image is saved as 'figure 2.png' inside the 'Images' folder.]")
                
            st.markdown("""
            Figure 2 provides a detailed map of this continuous cycle of learning. Here is how the steps connect:

            *   **Goal setting:** Effective evaluation always starts here. If you don't concretise what you want to achieve, your later actions might not align with your true aims.
            *   **Collecting or selecting data:** Your goals determine exactly what information you need to gather to get a grip on your educational practices.
            *   **Read, explore, and discuss:** Before jumping to conclusions, teams should look at the raw information together. 
            *   **Analysis and Interpretation:** This is where you figure out the story the data is telling you.
            *   **Diagnosis:** If the results show a specific problem or success, you need to understand *why* it happened. This sub-process starts when you **formulate a hypothesis** (an educated guess about the cause). You might need to **collect additional data** to test this guess. Once you reach a final **interpretation and conclusion** about the root cause, the diagnosis is complete.
            *   **Action planning, implementation, and action evaluation:** With the root causes confirmed, you can plan your next steps, put them into practice, and evaluate if those new actions actually worked.

            **A note on real life:** In daily practice, teams might enter this cycle at different points. You might already have data available and start straight at analysis, or you might occasionally skip a step. That is completely normal. 
            
            The figure isn't a strict rulebook; it simply visualises the essential steps needed to turn raw data into meaningful information and deep knowledge. Ultimately, moving systematically through this cycle fosters a culture of joint reflection and learning within your team.
            
            ---
            **References for this section:**<br>
            *<small> [1] Lai, M.K. and K. Schildkamp (2013). Data-based Decision Making: An Overview.<br>[2] Hoefkens, A., et al. (2024). Dashboards en e-courses als ondersteuning voor onderwijsprofessionals bij datagebruik.<br>[3] Schildkamp, K., C.L. Poortman, and A. Handelzalts (2016). Data teams for school improvement.</small>*
            """, unsafe_allow_html=True)


        with st.expander("Assessment model and conceptual basis (What is SCCE?)"):
            st.markdown("""
            Sustainability and Climate Change Education (<abbr title="Sustainability and Climate Change Education">SCCE</abbr>) relates to enabling learners to take pro-sustainability, pro-environmental, and climate-friendly action. <abbr title="Sustainability and Climate Change Education">SCCE</abbr> aims to equip all learners with the knowledge, skills, and attitudes needed to contribute to the green transition and sustainable development.
            
            By fostering <abbr title="The ability of learners to take meaningful action on sustainability issues.">Action Competence</abbr> via an action-oriented approach, <abbr title="Sustainability and Climate Change Education">SCCE</abbr> equips learners to become active agents of change in the transition toward a more just, peaceful, and sustainable world.
            
            ---
            **References for this section:**<br>
            *<small>[4] Council of the European Union, Council Recommendation of 16 June 2022 on learning for the green transition and sustainable development, in Official Journal of the European Union. 2022.</small>*
            """, unsafe_allow_html=True)

            
        with st.expander("What is Action Competence?"):
            st.markdown("""
            A well-established goal of <abbr title="Sustainability and Climate Change Education">SCCE</abbr> is building **Action Competence**. This means helping learners develop the ability to take meaningful action on sustainability or societal issues. It goes beyond just changing behaviour (like following a rule); it is about acting voluntarily with a clear, sustainable purpose.
            
            In education, fostering action competence means helping students not just learn about problems, but feeling empowered to actually do something about them. As shown in Figure 3, it is built on three essential components:
            """, unsafe_allow_html=True)
            
            # Pointing the app to the Images subfolder for Figure 3
            try:
                st.image("Images/figure 3.png", caption="Figure 3: The three components of Action Competence", width=500)
            except FileNotFoundError:
                st.info("🖼️ [Image Placeholder: Make sure the action competence image is saved as 'figure 3.png' inside the 'Images' folder.]")

            st.markdown("""
            ### The Three Components
            *   **Knowledge of action possibilities:** Understanding the issue at hand - its causes, consequences, and potential solutions. You don't need highly technical or scientific knowledge to be "action competent." It is more about having the skills to find reliable information, reflect on it critically, and know *how* to take well-informed actions.
            *   **Willingness to act:** Feeling motivated and genuinely wanting to make a difference. Learners are not only aware of the issues; they are passionate, dedicated, and committed to taking action.
            *   **Confidence in own influence:** Believing that your actions matter. This has two sides: feeling capable of successfully carrying out the action (self-efficacy), and trusting that the action will actually lead to the desired result (outcome expectancy).
            
            ---
            
            ### Individual vs. Collective Action
            Action competence can manifest at two levels: as an individual or as a group. Here is what that looks like in practice:
            
            **1. Knowledge of action possibilities**
            *   *Individual:* Knowing what actions you can take yourself, such as choosing sustainable travel options for a holiday.
            *   *Collective:* Knowing about actions that require group effort, like organising a petition for better train connections across Europe.
            
            **2. Willingness to act**
            *   *Individual:* Being eager to reduce your own plastic use and actively looking for alternatives in daily life.
            *   *Collective:* A group of teachers feeling motivated to rethink a school project to better align with sustainability goals.
            
            **3. Confidence in influence**
            *   *Individual:* Believing you can successfully switch to biking instead of driving to school, and feeling capable of making that change.
            *   *Collective:* Students feeling confident that, by working together, they can persuade the school board to install more bike racks. (Or a group of teachers feeling confident they can collaborate to design a new curriculum).
            """)

            st.markdown("---")
            st.success("""
            **The Ultimate Goal:** Within the IMP>ACT assessment framework, Action Competence (AC) is regarded as the key desired outcome. Therefore, when evaluating the impact of your initiatives, these three components serve as your central indicators of success.
            """)
            
            st.markdown("""
            ---
            **References for this section:**<br>
            *<small>[5] Sass, W., et al. (2020). Redefining action competence: the case of sustainable development.<br>[6] Marcelino, B.G.P.U.C.G. (2022). GreenComp: The European sustainability competence framework.</small>*
            """, unsafe_allow_html=True)

        with st.expander("What is Action-Oriented SCCE & Educator Competencies?"):
            st.markdown("""
            If Action Competence is the *goal*, **Action Orientation (AO)** is the *method*. It is the teaching approach designed to help learners actually develop that competence. 
            
            Action-oriented <abbr title="Sustainability and Climate Change Education">SCCE</abbr> emphasises meaningful actions and long-term solutions. But it is not just about taking action—it also involves deep reflection and helping learners navigate the complex, sometimes negative emotions that come with facing real-world climate challenges.
            
            To guide educators, this approach relies on **five pedagogical principles**:
            """, unsafe_allow_html=True)
            
            # Pointing the app to the Images subfolder for Figure 4
            try:
                st.image("Images/figure 2.png", caption="Figure 2: Data use circle of inquiry, modelled on Hoefkens et al., (2024)", width=650)
            except FileNotFoundError:
                st.info("🖼️ [Image Placeholder: Make sure the image is saved as 'figure 2.png' inside the 'Images' folder.]")


            st.markdown("""
            ### The Five Principles in Practice
            *   **Learning through action:** Learners don't just read about issues; they actively solve challenges through real actions (individual, collective, or political). This creates a positive loop: acting builds competence, which empowers them to take even more effective actions later.
            *   **Real-world integration:** Education steps outside the classroom. Learners tackle real sustainability challenges in collaboration with their local community, making the lessons relevant and purposeful.
            *   **Critical reflection:** Learners take an active role in making decisions. Through reflection, they clarify their own underlying values, beliefs, and assumptions about sustainability.
            *   **Emotional awareness:** Climate issues can be overwhelming. Educators provide a supportive environment, guiding learners to process the wide range of emotions (both positive and negative) that arise.
            *   **Democratic participation:** Learners get a seat at the table. Through dialogue and shared responsibility, they are empowered to shape their own learning and contribute meaningfully to the solutions.
            
            ---
            
            ### What Competencies Do Educators Need?
            To bring this action-oriented approach to life, educators themselves need a specific set of professional tools and mindsets. We break these down into three main areas:
            
            **1. Professional Knowledge**
            *   **Content Knowledge (CK):** Knowing the facts. Understanding climate issues, causes, solutions, and future visions.
            *   **Pedagogical Content Knowledge (PCK):** Knowing *how* to teach it. Using engaging, inclusive methods that fit the learners' needs and addressing common misconceptions.
            *   **Institutional Context Knowledge (ICK):** Knowing how to navigate the school system. Acting as a change agent to embed sustainability across the whole school and collaborate with colleagues.
            
            **2. Self-Efficacy (Confidence)**
            Educators need to believe they can make a difference. This means feeling confident in their ability to help students build skills (like systems thinking) and believing they can successfully promote broader change within their institution.
            
            **3. Willingness to Implement (Motivation)**
            This involves the drive to teach sustainability, which can come from within (intrinsic motivation: teaching it because it feels deeply meaningful) or from outside (extrinsic motivation: driven by school policies or societal expectations).
            """)

            st.markdown("---")
            st.success("""
            **The Ultimate Goal:** Within the IMP>ACT framework, these five components of **Action Orientation** are the main engine for driving a learner's Action Competence. When you evaluate your SCCE initiatives, both this pedagogical approach and your educators' competencies will serve as crucial indicators of success.
            """)
            
            st.markdown("""
            ---
            **References for this section:**<br>
            *<small>[7] Sinakou, E., et al. (2019). Designing Powerful Learning Environments in Education for Sustainable Development: A Conceptual Framework.</small>*
            """, unsafe_allow_html=True)

        with st.expander("Guiding Principles of the IMP>ACT Framework"):
            st.markdown("""
            As an end user, it is up to you to engage in thoughtful reflection on the information and questions presented in this tool. 
            
            Keep the following 9 principles of the IMP>ACT framework in mind as you proceed:
            
            1. **Programmatic focus, not learner assessment:** We are assessing educational programmes, not grading individual learners.
            2. **Outcomes over outputs:** What is learned matters more than how many people attended a course or program.
            3. **What is measured signals what matters:** IMP>ACT promotes the development of action competence, more than merely changing behaviour.
            4. **No single learning goal applies universally:** While action competence is important, you can find other things important for your organisation as well.
            5. **Emphasis on user validity:** What matters for users reflects what is deemed valid.
            6. **Emphasis on methodological validity:** All assessment tools in the framework are developed using high academic standards.
            7. **Co-designed assessment implementation:** There is no one-size-fits-all solution; it is a framework requiring collaboration and reflection to design the assessment.
            8. **Quality improvement and accountability:** The framework spans improving and proving the value of SCCE programs.
            9. **Feedback loops:** The framework is not a linear path; it promotes participatory feedback loops between the different stages of the assessment process.
            """)

        st.markdown("---")
        
        # --- INTERACTIVE REFLECTION SECTION ---
        st.subheader("✍️ Reflection & Application")
        st.markdown("Use the following questions to reflect on the use of the framework within your specific context.")

        st.markdown("#### General Framework Application")
        q1 = "What would you like to achieve by using the IMP>ACT framework in your organisation? (Select all that apply)"
        options_q1 = ["Accountability", "Quality development", "Accreditation", "User-satisfaction", "Other"]
        saved_a1 = load_answer(conn, user, "Module 1", q1)
        default_a1 = saved_a1.split("||") if saved_a1 else []
        valid_defaults = [opt for opt in default_a1 if opt in options_q1]
        a1_raw = st.multiselect(q1, options_q1, default=valid_defaults)
        a1 = "||".join(a1_raw)
        
        q1b = "Please explain your objectives in more detail:"
        a1b = st.text_area(q1b, value=load_answer(conn, user, "Module 1", q1b))

        # Re-integrating the image for Question 2
        st.markdown("---")
        st.markdown("#### The Data Use Cycle")
        try:
            st.image("Images/figure 2.png", caption="Figure 2: Data use circle of inquiry", width=650)
        except FileNotFoundError:
            st.info("🖼️ [Image Placeholder: Save the cycle image as 'figure 2.png' inside the 'Images' folder to display it here.]")
            
        q2 = "Where would you situate your organisation in the cycle of data use?"
        cycle_options = [
            "Select your current stage...",
            "Goal setting",
            "Collecting or selecting data",
            "Read, explore and discuss",
            "Interpretation",
            "Diagnosis",
            "Formulate hypothesis",
            "Collect additional data",
            "Analysis",
            "Interpretation and conclusion",
            "Action planning",
            "Action implementation",
            "Action evaluation"
        ]
        
        saved_a2 = load_answer(conn, user, "Module 1", q2)
        cycle_index = cycle_options.index(saved_a2) if saved_a2 in cycle_options else 0
        
        a2 = st.selectbox(q2, cycle_options, index=cycle_index)

        # --- DYNAMIC ROUTING ADVICE ---
        if a2 != "Select your current stage...":
            if a2 in ["Goal setting", "Collecting or selecting data"]:
                st.info("🗺️ **Suggested Pathway:** Since you are at the beginning of the cycle, we recommend working through the framework sequentially. Start with Module 2 to discover your organisational persona, then proceed to Module 3 (Goal Setting) and so on.")
            elif a2 in ["Read, explore and discuss", "Interpretation", "Diagnosis", "Formulate hypothesis", "Collect additional data", "Analysis"]:
                st.info("🗺️ **Suggested Pathway:** You are deep in the exploration and analysis phase! You might want to jump directly to **Module 4 (Backing of Claims)** and **Module 5 (Indicators)** to evaluate how you are handling your data.")
            elif a2 == "Interpretation and conclusion":
                st.info("🗺️ **Suggested Pathway:** You are ready to draw conclusions! You can jump directly to **Module 6 (Interpreting data and information)**.")
            elif a2 == "Action planning":
                st.info("🗺️ **Suggested Pathway:** You are ready to act! You can jump directly to **Module 7 (Action planning)**.")
            elif a2 in ["Action implementation", "Action evaluation"]:
                st.info("🗺️ **Suggested Pathway:** You have reached the end of a cycle! You can either head to the **Summary & Export** to finalize your current project, or start a brand new cycle with new goals.")
            
            st.success("""
            💡 **Pro Tip:** No matter where you are in the cycle, we highly recommend completing **Module 2: Your Organisation** first, as your persona will inform the rest of your choices. 
            
            *Remember: Filling in the reflection questions across all modules creates a complete, exportable logbook of your assessment design!*
            """)

        st.markdown("---")
        q3 = "What are your expectations for using the IMP>ACT framework in your organisation?"
        a3 = st.text_area(q3, value=load_answer(conn, user, "Module 1", q3))
        
        q4 = "What are potential pitfalls using the IMP>ACT framework in your organisation?"
        a4 = st.text_area(q4, value=load_answer(conn, user, "Module 1", q4))

        col1, col2 = st.columns(2)
        with col1:
            q5 = "Partners & stakeholders WITHIN your organisation:"
            a5 = st.text_area(q5, value=load_answer(conn, user, "Module 1", q5))
        with col2:
            q6 = "Partners & stakeholders OUTSIDE your organisation:"
            a6 = st.text_area(q6, value=load_answer(conn, user, "Module 1", q6))

        st.markdown("---")
        st.markdown("#### SCCE Alignment")
        q7 = "To what extent does the organisational perspective on SCCE align with the description of SCCE given in this tool?"
        a7 = st.text_area(q7, value=load_answer(conn, user, "Module 1", q7))
        
        q8 = "Are there any other theoretical perspectives that your organisation uses when working with SCCE that were not mentioned above?"
        a8 = st.text_area(q8, value=load_answer(conn, user, "Module 1", q8))

        st.markdown("---")
        st.markdown("#### Action Competence Outcomes")
        q9 = "What does action competence look like in your case? Map the intended learning outcomes of your SCCE onto action competence:"
        a9 = st.text_area(q9, value=load_answer(conn, user, "Module 1", q9))
        
        q10 = "What in your SCCE activities contributes to learners’ action competence?"
        a10 = st.text_area(q10, value=load_answer(conn, user, "Module 1", q10))
        
        q11 = "What else is there? Which of your intended SCCE learning outcomes do not match with action competence?"
        a11 = st.text_area(q11, value=load_answer(conn, user, "Module 1", q11))

        st.markdown("---")
        st.markdown("#### Action-Oriented SCCE & Educator Competencies")
        q12 = "To what extent does the organisational perspective on teaching SCCE in an action-oriented way align with the description of Action Orientation given in this document?"
        a12 = st.text_area(q12, value=load_answer(conn, user, "Module 1", q12))
        
        q13 = "How do the different pedagogical principles described above look like in your case?"
        a13 = st.text_area(q13, value=load_answer(conn, user, "Module 1", q13))
        
        q14 = "Map the required educator competences to your activities. To what extent are the competencies for educators mentioned above recognised within your organisation?"
        a14 = st.text_area(q14, value=load_answer(conn, user, "Module 1", q14))
        
        q15 = "Do you value or promote additional competencies among your educators?"
        a15 = st.text_area(q15, value=load_answer(conn, user, "Module 1", q15))

        if st.button("Save Module 1"):
            save_answer(conn, user, "Module 1", q1, a1)
            save_answer(conn, user, "Module 1", q1b, a1b)
            save_answer(conn, user, "Module 1", q2, a2)
            save_answer(conn, user, "Module 1", q3, a3)
            save_answer(conn, user, "Module 1", q4, a4)
            save_answer(conn, user, "Module 1", q5, a5)
            save_answer(conn, user, "Module 1", q6, a6)
            save_answer(conn, user, "Module 1", q7, a7)
            save_answer(conn, user, "Module 1", q8, a8)
            save_answer(conn, user, "Module 1", q9, a9)
            save_answer(conn, user, "Module 1", q10, a10)
            save_answer(conn, user, "Module 1", q11, a11)
            save_answer(conn, user, "Module 1", q12, a12)
            save_answer(conn, user, "Module 1", q13, a13)
            save_answer(conn, user, "Module 1", q14, a14)
            save_answer(conn, user, "Module 1", q15, a15)
            
            st.session_state['save_success'] = 'Module 1'
            st.rerun() 

        if st.session_state.get('save_success') == 'Module 1':
            st.success("✅ Module 1 reflections saved successfully!")
            st.session_state['save_success'] = None

    # --- MODULE 2 ---
    elif module == "2. Your Organisation":
        st.title("Module 2: Your Organisation")
        
        st.markdown("""
        ### Who are we as an organisation?
        The IMP>ACT framework is designed to be used by a wide range of organisations involved in <abbr title="Sustainability and Climate Change Education">SCCE</abbr>. Rather than offering a fixed model, the framework encourages adaptation and inspiration. Organisations can reflect on their own context while learning from the experiences and approaches of others. This openness supports user validity, allowing each organisation to shape the framework in ways that are meaningful and relevant to their mission.
        """, unsafe_allow_html=True)
        
        st.info("""
        **🔗 Why start here instead of Goal Setting?**
        You might wonder why we are looking at organisational identity before jumping straight into goal setting (Module 3). The answer is simple: **your context shapes your goals**. By first understanding your specific role, capacity, and target audience within the SCCE landscape, you ensure that the goals you set in the next step are realistic, relevant, and perfectly tailored to your unique mission.
        """)
        
        st.markdown("""
        To support diverse organisations in applying the IMP>ACT framework meaningfully, we introduce **personas**. These fictional but realistic profiles represent different types of organisations active in SCCE. 
        
        Each persona illustrates a specific organisational type, including their goals, challenges, and typical practices.
        
        **Why Use Personas?**
        * **Clarify your own identity:** Comparing your organisation to a persona helps you better understand your role and focus within SCCE.
        * **Stimulate reflection:** Personas prompt critical thinking about your strengths, needs, and opportunities for growth.
        * **Encourage adaptation:** Seeing how others approach SCCE can inspire new strategies or adaptations of the framework.
        * **Support user validity:** Personas help ensure that the framework is interpreted and used in ways that are relevant to your context.
        
        *These personas are not fixed categories, but rather starting points for reflection and inspiration. Your organisation may identify strongly with one persona or see elements of several. The goal is not to fit into a box, but to use the personas to better understand your position and explore possibilities.*
        """)

        # --- LEAF SYMBOLISM EXPLANATION ---
        st.markdown("<br>", unsafe_allow_html=True) # Adds a little breathing room
        with st.expander("🌿 Why leaves? The symbolism behind our personas"):
            st.markdown("""
            Because the IMP>ACT framework is deeply rooted in **Sustainability and Climate Change Education (SCCE)**, we chose to represent our personas using botanical elements rather than generic corporate avatars. 
            
            Leaves are universal symbols of growth, renewal, and connection to nature. We paired each persona with a specific leaf whose natural characteristics mirror the organisation's core mission:
            
            *   🍁 **The Maple (SCCE Evidence Provider):** The maple's broad, multi-lobed structure represents the diversity of educational segments it spans. It acts as a foundational "backbone" leaf, suggesting stability, broad support, and evidence-based growth.
            *   🌳 **The Oak (SCCE Program Provider):** With its deep, distinctive lobes, the oak conveys focus, depth, and unwavering commitment. It represents an organisation dedicated to doing one thing—delivering specific SCCE programs—exceptionally well.
            *   🌿 **The Ash (The All-Round Supplier):** The ash is a compound leaf (multiple smaller leaflets attached to one central stem). This beautifully represents diverse, adaptable educational activities unified under one single organisational umbrella.
            *   🍃 **The Ivy (SCCE Network Provider):** The ivy leaf, with its dynamic form reaching outward, is nature's ultimate symbol of connection. It perfectly captures an organisation that links, bridges, and brings disparate practices and professionals together.
            """)

        st.markdown("---")
        st.subheader("🧩 Persona Discovery Quiz")
        st.markdown("Answer the four questions below to determine which persona best fits your organisation.")

        persona_map = {
            "A": "SCCE Evidence Provider",
            "B": "SCCE Program Provider",
            "C": "The All-Round Supplier",
            "D": "SCCE Network Provider"
        }

        with st.form("persona_quiz"):
            q1_label = "1. What is the core mission of your daily work?"
            opt1 = [
                "A: We aim to support, guide, and monitor educational programs across the broader sector.",
                "B: We are focused on delivering specific learning activities directly to participants to foster sustainability.",
                "C: We offer a wide variety of learning programs, and sustainability is just one topic among many.",
                "D: We act as a bridge, connecting professionals, organizations, and good practices with one another."
            ]
            ans1 = st.radio(q1_label, opt1)

            q2_label = "2. Who is your primary target audience?"
            opt2 = [
                "A: Policymakers, large-scale educational sectors, and program coordinators.",
                "B: The specific learners participating in our activities and the educators delivering them.",
                "C: A broad, diverse group of learners engaging in our general educational or cultural offerings.",
                "D: Other organizations, schools, networks, and professional communities."
            ]
            ans2 = st.radio(q2_label, opt2)

            q3_label = "3. What is your main goal for conducting an impact assessment?"
            opt3 = [
                "A: To monitor quality across the field and build an evidence base for what effective SCCE looks like on a large scale.",
                "B: To evaluate and improve our specific activities, and to prove our value to our funders and participants.",
                "C: To figure out how to integrate SCCE evaluation effectively without narrowing our broader organizational portfolio.",
                "D: To spot good practices so we can share them and strengthen assessment capacity across our partner network."
            ]
            ans3 = st.radio(q3_label, opt3)

            q4_label = "4. Which slogan resonates most with your organization?"
            opt4 = [
                "A: 'We support SCCE with the aim of a sustainable transition of society.'",
                "B: 'With our SCCE-activities, we can contribute to a sustainable society.'",
                "C: 'SCCE is a part of our diverse learning portfolio.'",
                "D: 'Connecting people and practices for stronger SCCE.'"
            ]
            ans4 = st.radio(q4_label, opt4)

            submitted = st.form_submit_button("Calculate Persona")

        if submitted:
            scores = {"A": 0, "B": 0, "C": 0, "D": 0}
            scores[ans1[0]] += 1
            scores[ans2[0]] += 1
            scores[ans3[0]] += 1
            scores[ans4[0]] += 1
            
            primary_letter = max(scores, key=scores.get)
            primary_persona = persona_map[primary_letter]
            
            save_answer(conn, user, "Module 2", "Calculated Persona", primary_persona)
            st.success("Quiz complete! Scroll down to see your detailed results.")

        st.markdown("---")
        saved_persona = load_answer(conn, user, "Module 2", "Calculated Persona")
        
        
        # --- DETAILED PERSONA PROFILES ---
        def display_persona_details(p_name):
            if p_name == "SCCE Evidence Provider":
                col1, col2 = st.columns([1, 3])
                with col1:
                    try:
                        st.image("Images/Maple_Orange.jpg", use_container_width=True, caption="The Evidence Provider")
                    except FileNotFoundError:
                        st.info("🖼️ [Save 'Maple_Orange.jpg' in Images]")
                with col2:
                    st.markdown("**Slogan:** *'We support SCCE with the aim of a sustainable transition of society'*")
                    st.markdown("**Description:** The supporting organisation aims to support, guide and monitor programs for SCCE across the broad educational sector (from compulsory education to higher education and non-formal education).")
                    st.markdown("**Goals for doing impact assessment:**")
                    st.markdown("""
                    * Learn (others) what effective SCCE entails and how to promote it across contexts.
                    * Monitor the quality of SCCE activities to identify strengths and areas for improvement.
                    * Support programs and partners by sharing good practices and enhancing their impact.
                    * Demonstrate and strengthen the societal relevance of SCCE through evidence-based impact reporting.
                    """)
                    st.markdown("**Target groups:**")
                    st.markdown("""
                    * Professionals: teachers, educators, school leaders, teacher trainers, NGO facilitators.
                    * Learners: pupils, students, adult learners.
                    * Organizations: schools, universities, NGOs, teacher training institutes.
                    """)
                    
            elif p_name == "SCCE Program Provider":
                col1, col2 = st.columns([1, 3])
                with col1:
                    try:
                        st.image("Images/Oak_DarkGreen.jpg", use_container_width=True, caption="The Program Provider")
                    except FileNotFoundError:
                        st.info("🖼️ [Save 'Oak_DarkGreen.jpg' in Images]")
                with col2:
                    st.markdown("**Slogan:** *'With our SCCE-activities, we can contribute to a sustainable society'*")
                    st.markdown("**Description:** Focused on delivering SCCE learning activities. They aim to influence learners’ actions, not just knowledge. Curious about impact to improve programs and build credibility. Sometimes need to report to funders.")
                    st.markdown("**Goals for doing impact assessment:**")
                    st.markdown("""
                    * (Learn how to) measure and understand the impact of SCCE activities.
                    * Monitor and improve the effectiveness of activities.
                    * Use evidence to strengthen quality care.
                    * Demonstrate societal value and build a credible reputation.
                    """)
                    st.markdown("**Target groups:**")
                    st.markdown("""
                    * Learners: people participating in the SCCE-activities.
                    * Educators: people teaching and organising the SCCE-activities.
                    """)

            elif p_name == "The All-Round Supplier":
                col1, col2 = st.columns([1, 3])
                with col1:
                    try:
                        st.image("Images/Ash_SlateBlue.jpg", use_container_width=True, caption="The All-Round Supplier")
                    except FileNotFoundError:
                        st.info("🖼️ [Save 'Ash_SlateBlue.jpg' in Images]")
                with col2:
                    st.markdown("**Slogan:** *'SCCE is a part of our diverse learning portfolio'*")
                    st.markdown("**Description:** Offers a broad range of learning activities, with SCCE as one element among others. SCCE is not their core focus but an important part of their portfolio.")
                    st.markdown("**Goals for doing impact assessment:**")
                    st.markdown("""
                    * Clarify SCCE objectives within broader programs.
                    * (Learn how to) evaluate SCCE effectively.
                    * Integrate SCCE without narrowing the overall program scope.
                    * Use SCCE assessment as a lever for broader evaluation practices.
                    """)
                    st.markdown("**Target groups:**")
                    st.markdown("""
                    * Learners: people participating in the (SCCE-)activities.
                    * Educators: people teaching and organising the (SCCE-) activities.
                    """)

            elif p_name == "SCCE Network Provider":
                col1, col2 = st.columns([1, 3])
                with col1:
                    try:
                        st.image("Images/Ivy.jpg", use_container_width=True, caption="The Network Provider")
                    except FileNotFoundError:
                        st.info("🖼️ [Save 'Ivy.jpg' in Images]")
                with col2:
                    st.markdown("**Slogan:** *'Connecting people and practices for stronger SCCE.'*")
                    st.markdown("**Description:** Connects organizations, professionals, and learners with relevant SCCE programs, resources, and assessment practices. Acts as a bridge to share expertise and foster collaboration.")
                    st.markdown("**Goals for doing impact assessment:**")
                    st.markdown("""
                    * Spot and share good practices.
                    * Connect organizations in developing assessment capacity.
                    * Strengthen SCCE networks and partnerships.
                    * Promote quality and consistency in SCCE implementation.
                    """)
                    st.markdown("**Target groups:**")
                    st.markdown("""
                    * Organizations: schools, universities, NGOs, teacher training institutes.
                    """)

        if saved_persona:
            st.subheader("🎉 Your Dominant Persona Is:")
            st.info(f"### {saved_persona}")
            display_persona_details(saved_persona)

            st.markdown("---")
            st.markdown("#### Explore the other Personas:")
            for p_name in persona_map.values():
                if p_name != saved_persona:
                    with st.expander(f"View details for: {p_name}"):
                        display_persona_details(p_name)

            # --- PDF DOWNLOAD BUTTON (Moved to the bottom!) ---
            st.markdown("---")
            try:
                with open("personas_overview.pdf", "rb") as pdf_file:
                    PDFbyte = pdf_file.read()
                st.download_button(
                    label="📄 Download the Personas Overview Table (PDF)",
                    data=PDFbyte,
                    file_name="IMP_ACT_Personas_Overview.pdf",
                    mime='application/octet-stream'
                )
            except FileNotFoundError:
                # Fallback text version if the PDF is not in the folder yet
                fallback_text = """IMP>ACT Organisational Personas Overview\n\n1. SCCE Evidence Provider\n- Slogan: "We support SCCE with the aim of a sustainable transition of society"\n- Description: Aims to support, guide and monitor programs for SCCE across the broad educational sector.\n\n2. SCCE Program Provider\n- Slogan: "With our SCCE-activities, we can contribute to a sustainable society"\n- Description: Focused on delivering SCCE learning activities to influence learners' actions.\n\n3. The All-Round Supplier\n- Slogan: "SCCE is a part of our diverse learning portfolio"\n- Description: Offers a broad range of learning activities, with SCCE as one element among others.\n\n4. SCCE Network Provider\n- Slogan: "Connecting people and practices for stronger SCCE."\n- Description: Connects organizations, professionals, and learners with relevant SCCE programs and resources."""
                st.download_button(
                    label="📄 Download the Personas Overview Table (Text Version)",
                    data=fallback_text,
                    file_name="IMP_ACT_Personas_Overview.txt",
                    mime='text/plain'
                )
                st.caption("*(Note: To enable the PDF download, simply save your table as a PDF named 'personas_overview.pdf' in the same folder as this app.)*")

            # --- REFLECTION QUESTIONS ---
            st.markdown("---")
            st.subheader("✍️ Organisational Reflection")

            q_align = "What aspects of the persona description feel most accurate for your organization? Which feel less relevant?"
            a_align = st.text_area(q_align, value=load_answer(conn, user, "Module 2", q_align))
            
            q_other = "Are there elements from other personas that also apply to your organization? If yes, which ones and why?"
            a_other = st.text_area(q_other, value=load_answer(conn, user, "Module 2", q_other))

            # --- NEW CAPACITY THEORY SECTION ---
            st.markdown("---")
            st.subheader("📊 Organisational Capacity for Assessment")
            
            with st.expander("What is your organisational capacity for assessment?"):
                st.markdown("""
                The fact that you are using this framework shows that your organisation cares about the quality of <abbr title="Sustainability and Climate Change Education">SCCE</abbr>, and how assessment can help improve it. 
                
                Just as organisations differ in their goals and target audiences (as seen in the personas), they also differ in their **organisational capacity for assessment**. 
                
                ### What does "capacity" mean?
                Capacity simply refers to how ready and able your organisation is to plan, carry out, and learn from assessments. This includes having:
                * **The right people and skills:** Staff with experience or training in evaluation.
                * **The right tools:** Systems or routines in place to collect data.
                * **The right mindset:** A culture that uses assessment results to actively improve work, rather than just ticking a box.
                
                For some organisations, impact assessment is entirely new territory. For others, it is a deeply embedded routine.
                
                ### The Assessment Continuum
                Figure 6 below illustrates the stages of organisational capacity. The continuum ranges from **Emerging** (just starting out) to **Strategic** (highly integrated and adaptive). 
                
                *Note: This is **not a judgment tool!** It is simply a starting point for dialogue. Identifying where you currently stand helps you spot strengths, acknowledge gaps, and plan for realistic growth.*
                """, unsafe_allow_html=True)
                
                try:
                    st.image("Images/figure 6.png", caption="Figure 6: Stages of organisational capacity for assessment", width=700)
                except FileNotFoundError:
                    st.info("🖼️ [Image Placeholder: Save the capacity image as 'figure 6.png' inside the 'Images' folder.]")

            # --- NEW CAPACITY REFLECTION QUESTIONS ---
            st.markdown("#### Reflect on your capacity")
            
            q_capacity = "1. Where would you situate the capacity for assessment within your organisation? (For self-reflection only—there are no right or wrong answers!)"
            options_cap = ["Select a stage...", "Emerging", "Basic", "Developing", "Established", "Strategic"]
            saved_cap = load_answer(conn, user, "Module 2", q_capacity)
            cap_index = options_cap.index(saved_cap) if saved_cap in options_cap else 0
            a_capacity = st.selectbox(q_capacity, options_cap, index=cap_index)
            
            q_cap_why = "Why did you choose this stage?"
            a_cap_why = st.text_area(q_cap_why, value=load_answer(conn, user, "Module 2", q_cap_why))
            
            q_expertise = "2. Who in your organisation has expertise in or experience with assessment? (Think about staff members who have worked on evaluating programs, collecting feedback, or measuring outcomes.)"
            a_expertise = st.text_area(q_expertise, value=load_answer(conn, user, "Module 2", q_expertise))
            
            q_external = "3. Are there external partners that could aid in building this capacity? (Consider collaborating with universities, consultants, or peer organisations with experience in impact assessment.)"
            a_external = st.text_area(q_external, value=load_answer(conn, user, "Module 2", q_external))

            # --- UPDATED SAVE BUTTON ---
            if st.button("Save Module 2"):
                save_answer(conn, user, "Module 2", q_align, a_align)
                save_answer(conn, user, "Module 2", q_other, a_other)
                save_answer(conn, user, "Module 2", q_capacity, a_capacity)
                save_answer(conn, user, "Module 2", q_cap_why, a_cap_why)
                save_answer(conn, user, "Module 2", q_expertise, a_expertise)
                save_answer(conn, user, "Module 2", q_external, a_external)
                
                st.session_state['save_success'] = 'Module 2'
                st.rerun()

            if st.session_state.get('save_success') == 'Module 2':
                st.success("✅ Module 2 reflections saved successfully!")
                st.session_state['save_success'] = None


    # --- MODULE 3 ---
    elif module == "3. Goal Setting":
        st.title("Module 3: Goal Setting")
        st.markdown("Setting up an assessment will often start with reflecting and formulating the goals of the assessment: what does the organisation want to achieve with the assessment? This step is crucial to avoid overshooting. Without clearly defined and realistic goals, organisations may end up collecting data that doesn’t serve their mission or make decisions based on flawed assumptions.")
        
        st.subheader("📚 Core Concepts & Guidelines")
        
        with st.expander("Why goal setting matters & Strategic Drivers"):
            st.markdown("""
            Using data without clear goals is a common and often counterproductive practice.
            
            Assessment goals are often embedded within the broader strategic vision and mission of an organisation. These **strategic drivers** for assessment may include:
            * **Quality development:** improving the design and delivery of <abbr title="Sustainability and Climate Change Education">SCCE</abbr> activities.
            * **Accountability:** demonstrating effectiveness to funders, partners, or stakeholders.
            * **Monitoring:** tracking progress over time or across different groups.
            * **Program evaluation:** understanding what works, for whom, and under what conditions.
            * **Certification or recognition:** validating competencies or achievements of participants.
            
            By explicitly formulating these strategic drivers, organisations strengthen user validity: they clarify *why* assessment is being conducted, how results will be interpreted, and how findings align with their mission.
            """, unsafe_allow_html=True)
            
            st.warning("""
            **💡 Case Study: Building Sustainable Futures**
            
            *Building Sustainable Futures* is an SCCE-program provider offering guided sustainability walks to local schools. Eager to demonstrate their impact, they set an ambitious assessment goal: **tracking participants’ action competence and identifying trends across the city.**
            
            While this reflects a strong commitment, it is misaligned with their role. As a provider of short, one-off activities, measuring long-term city-wide impact is difficult and not directly relevant to their daily work.
            
            **A more meaningful goal:** Assess short-term changes in awareness, engagement, or motivation among participants immediately after the walk using simple reflection prompts. They can rely on existing data from local authorities for the broader city-wide context!
            """)
            
        with st.expander("Goals linked to the organisation (Levels & Examples)"):
            st.markdown("Goals can be situated at three different levels. Click through the tabs below to explore them and see real-world examples.")
            
            tab1, tab2, tab3 = st.tabs(["1. Activity Level", "2. Organisational Level", "3. Beyond the Organisation"])
            
            with tab1:
                st.markdown("""
                **Activity Level**
                Goals focused on improving specific activities or implementing systems of quality assurance. Assessments here aim to understand immediate learning outcomes, participant engagement, or the effectiveness of a single intervention. *(Especially relevant for SCCE-program providers and all-around suppliers).*
                
                **Examples:**
                * **Act4water (NGO):** Wants to investigate if one specific activity ('Waterwise school') enhances action competence among students, and if not, how to improve it.
                * **Frame2Sustain (Higher Ed Course):** Aims to investigate whether their design students feel action competent to contribute to a sustainable future after participating in the course.
                """)
                
            with tab2:
                st.markdown("""
                **Organisational Level**
                Goals focused on learning if programs work overall, what the organisation is good at, and if they are on track to fulfill their long-term mission. This helps build credibility and can be presented to partners or funders. *(Relevant for networking organisations, program providers, and all-round suppliers).*
                
                **Examples:**
                * **FUME (Nature Centre):** Aims to gain insight into the effectiveness of their pedagogical approach to improve it, while also using the results to report to governmental bodies.
                * **Mjako (NGO):** Wants to integrate small data collections into *all* their activities to spot patterns and trends in impact across their entire organisation.
                """)
                
            with tab3:
                st.markdown("""
                **Beyond the Organisation**
                Assessment serves broader goals within the SCCE ecosystem. The focus shifts to monitoring quality across the field, supporting partner practices, and identifying scalable good practices. *(Especially relevant for supporting and brokering organisations).*
                
                **Example:**
                * **Sustainable Education Centre:** Acts as an expertise centre and partner for other organisations. They aim to install a monitoring system to determine strengths, weaknesses, and spot good practices across the entire field of SCCE.
                """)
                
        with st.expander("Linking Personas to Assessment Goals"):
            st.markdown("""
            While organisational goals differ, the outcomes of interest might be very similar. An Evidence Provider might lean towards field-wide monitoring, while a Program Provider focuses on activity improvement, but both are ultimately looking at Action Competence.
            
            Here is a general mapping of how the different personas align with goal levels:
            """)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                try:
                    st.image("Images/Maple_Orange.jpg", use_container_width=True, caption="The Evidence Provider")
                except FileNotFoundError:
                    st.info("🖼️ [Save Maple_Orange.jpg]")
            with col2:
                st.markdown("**Evidence Provider:** Heavily focused on **Beyond Organisational Level** (Monitoring quality in the field, supporting partners, spotting good practices).")
                
            st.markdown("---")
            col3, col4 = st.columns([1, 4])
            with col3:
                try:
                    st.image("Images/Oak_DarkGreen.jpg", use_container_width=True, caption="The Program Provider")
                except FileNotFoundError:
                    st.info("🖼️ [Save Oak_DarkGreen.jpg]")
            with col4:
                st.markdown("**Program Provider:** Heavily focused on **Activity & Organisational Levels** (Improving specific activities, evaluating programs, proving value to society).")
                
            st.markdown("---")
            col5, col6 = st.columns([1, 4])
            with col5:
                try:
                    st.image("Images/Ash_SlateBlue.jpg", use_container_width=True, caption="The All-Round Supplier")
                except FileNotFoundError:
                    st.info("🖼️ [Save Ash_SlateBlue.jpg]")
            with col6:
                st.markdown("**All-Round Supplier:** Heavily focused on **Activity & Organisational Levels** (Integrating SCCE without narrowing programs, clarifying objectives).")
                
            st.markdown("---")
            col7, col8 = st.columns([1, 4])
            with col7:
                try:
                    st.image("Images/Ivy.jpg", use_container_width=True, caption="The Network Provider")
                except FileNotFoundError:
                    st.info("🖼️ [Save Ivy.jpg]")
            with col8:
                st.markdown("**Network Provider:** Focused on **Organisational & Beyond Levels** (Spotting good practices, connecting organisations).")

        st.markdown("---")
        
        # --- INTERACTIVE REFLECTION SECTION ---
        st.subheader("✍️ Reflection & Application")
        st.markdown("Reflect on the strategic drivers and specific goals of your organisation.")

        q_driver = "1. What is the strategic driver of your organisation in assessing the impact of SCCE? (Select all that apply)"
        options_driver = ["Quality development", "Accountability", "Monitoring", "Program evaluation", "Certification or recognition", "Other"]
        saved_driver = load_answer(conn, user, "Module 3", q_driver)
        default_driver = saved_driver.split("||") if saved_driver else []
        valid_default_driver = [opt for opt in default_driver if opt in options_driver]
        
        a_driver_raw = st.multiselect(q_driver, options_driver, default=valid_default_driver)
        a_driver = "||".join(a_driver_raw)
        
        q_level = "2. At what level are the organisational goals situated? (Select all that apply)"
        options_level = ["Activity Level", "Organisational Level", "Beyond the Organisation"]
        saved_level = load_answer(conn, user, "Module 3", q_level)
        default_level = saved_level.split("||") if saved_level else []
        valid_default_level = [opt for opt in default_level if opt in options_level]
        
        a_level_raw = st.multiselect(q_level, options_level, default=valid_default_level)
        a_level = "||".join(a_level_raw)

        q_level_explain = "3. Please explain your choice of level(s):"
        a_level_explain = st.text_area(q_level_explain, value=load_answer(conn, user, "Module 3", q_level_explain))

        q_feasible = "4. To what extent are the defined goals realistic and feasible within the locus of control of the organisation?"
        a_feasible = st.text_area(q_feasible, value=load_answer(conn, user, "Module 3", q_feasible))

        st.markdown("---")
        st.markdown("#### 🎯 Formulating your Organisational Goals")
        st.markdown("""
        This table is designed to help your organisation articulate the specific goals you want to achieve. Clearly stating your goals will help guide the selection of indicators, the type of evidence needed, and the interpretation of results.
        
        **Instructions:**
        Double-click any cell in the table below to type. You can add new rows by clicking the plus (+) icon at the bottom of the table, or delete rows by selecting them and pressing delete/backspace.
        """)
        
        # Load saved table data or create a default empty dataframe
        saved_table = load_answer(conn, user, "Module 3", "Goal_Table")
        if saved_table:
            df_goals = pd.read_json(io.StringIO(saved_table))
        else:
            df_goals = pd.DataFrame(
                [
                    {"Description": "", "Strategic driver": None, "Level": None, "Outcome at stake": ""},
                    {"Description": "", "Strategic driver": None, "Level": None, "Outcome at stake": ""}
                ]
            )
            
        # --- THE DATATYPE FIX ---
        # Force the dataframe to treat columns as flexible 'objects' instead of numbers
        df_goals = df_goals.astype(object)
        
        # Safely clean up any Pandas NaNs or leftover strings so Streamlit accepts them as true blanks
        df_goals = df_goals.fillna("TEMP_BLANK").replace(["TEMP_BLANK", "None", "nan"], None)
        df_goals["Strategic driver"] = df_goals["Strategic driver"].replace("", None)
        df_goals["Level"] = df_goals["Level"].replace("", None)
            
        # Display the interactive data editor
        edited_df = st.data_editor(
            df_goals, 
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Description": st.column_config.TextColumn("Goal Description (What do you want to achieve?)", width="large", default=""),
                "Strategic driver": st.column_config.SelectboxColumn("Strategic Driver", options=["Quality development", "Accountability", "Monitoring", "Program evaluation", "Certification"]),
                "Level": st.column_config.SelectboxColumn("Level", options=["Activity", "Organisational", "Beyond Organisation"]),
                "Outcome at stake": st.column_config.TextColumn("Outcome at stake (e.g., AC)", width="medium", default=""),
            }
        )

        if st.button("Save Module 3"):
            save_answer(conn, user, "Module 3", q_driver, a_driver)
            save_answer(conn, user, "Module 3", q_level, a_level)
            save_answer(conn, user, "Module 3", q_level_explain, a_level_explain)
            save_answer(conn, user, "Module 3", q_feasible, a_feasible)
            
            # Save the table as a JSON string
            table_json = edited_df.to_json(orient="records")
            save_answer(conn, user, "Module 3", "Goal_Table", table_json)
            
            st.session_state['save_success'] = 'Module 3'
            st.rerun()

        if st.session_state.get('save_success') == 'Module 3':
            st.success("✅ Module 3 reflections and goal table saved successfully!")
            st.session_state['save_success'] = None

    # --- MODULE 4 ---
    elif module == "4. Backing of Claims":
        st.title("Module 4: Defining what is needed: Backing of Claims")
        st.markdown("Once assessment goals are defined, organisations can begin identifying the kinds of claims they wish to make based on those goals and reflect on what evidence is needed to support them[cite: 7].")
        
        # --- THEORY SECTION ---
        st.subheader("📚 Core Concepts & Guidelines")
        
        with st.expander("What is User Validity?"):
            st.markdown("""
            **User validity** means making sure that an assessment methodology is actually helpful and makes sense for the people who use it, like teachers, students, NGO staff, or policymakers. It’s about checking whether the results and insights from the assessment are clear, relevant, and useful for their everyday work and decisions.
            
            This idea is especially important in <abbr title="Sustainability and Climate Change Education">SCCE</abbr>, where assessments often aim to support transformative learning, critical thinking, and action-oriented competencies. 
            
            The IMP>ACT framework treats validity not as a fixed property of a test, but as a **chain of reasoned claims** about how assessment results are interpreted and used. Each claim must be supported by evidence. For instance, if an assessment claims to measure students’ ability to engage in sustainable action, user validity requires that educators understand how the scores reflect that ability, and that the results are used to support, and not hinder, students’ development.
            
            *Enhancing user validity is the guiding thread throughout this framework. By reflecting on these questions, your organisation can determine what constitutes a valid approach for your specific context.*
            """, unsafe_allow_html=True)

        with st.expander("Defining the Evidence & Backing of Claims"):
            st.markdown("""
            In the IMP>ACT framework, **backing** refers to the amount and quality of evidence needed to support the claims you make based on assessment data. Collecting data is one thing; ensuring that this data and the interpretation of the data are suitable for the conclusions that you draw is another.
            
            The more ambitious or far-reaching the claims, the stronger the backing must be. Depending on your goals, you must make methodological choices regarding:
            1. **The amount of (different) data** used (e.g., generalisation, triangulation).
            2. **The type of data** (e.g., closely related to the intended use, standardisation).
            3. **The use of a priori criteria** (e.g., extrapolation).
            4. **Quality control** on criteria and scoring procedures (e.g., expert involvement, construct validity).
            """)
            
        # --- VISUAL CASE STUDY USING NEW ICONS ---
        st.markdown("#### 💡 Case Study: How Goals Dictate Backing")
        st.markdown("As illustrated by this example, different organisations might need a different level of backing, even though they are looking at similar indicators (measuring participants’ action competence).")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Low-Stakes: Internal Improvement**")
            try:
                st.image("Images/Oak_DarkGreen.jpg", width=120, caption="The Program Provider")
            except FileNotFoundError:
                pass
            st.markdown("**Organisation 1: SCCE Program Provider**")
            st.markdown("""
            Wants to assess action competence before and after an activity to help tailor the activity and inform in-house educators. 
            * **The Claim:** Participants have varying levels of competence.
            * **The Backing (Light/Moderate):** Since data is used internally for differentiation, a short self-assessment or informal observation tool is sufficient.
            """)
            
        with col2:
            st.error("**High-Stakes: External Reporting**")
            try:
                st.image("Images/Maple_Orange.jpg", width=120, caption="The Evidence Provider")
            except FileNotFoundError:
                pass
            st.markdown("**Organisation 2: SCCE Evidence Provider**")
            st.markdown("""
            Wants to demonstrate the effectiveness of a region-wide activity to funders.
            * **The Claim:** The activity leads to measurable improvement in participants' action competence.
            * **The Backing (Strong):** Because of external reporting and accountability, they need robust evidence like validated instruments, consistent pre/post measures, and comparative data.
            """)

        # --- DYNAMIC BACKING INTEGRATION ---
        st.markdown("---")
        st.subheader("🔗 Your Required Backing")
        
        # We silently retrieve the user's goal level from Module 3 to customize the UI
        m3_levels = load_answer(conn, user, "Module 3", "2. At what level are the organisational goals situated? (Select all that apply)")
        
        if "Beyond the Organisation" in m3_levels:
            st.error("""
            **High Backing Required (Beyond Organisational Level)**
            Your goals involve monitoring quality in the field or setting examples for others. Claims with such large implications require robust evidence, validated instruments, and high quality control.
            """)
        if "Organisational Level" in m3_levels:
            st.warning("""
            **Moderate to High Backing Required (Organisational Level)**
            Your goals involve defining strengths/weaknesses in programs, reporting to funders, or proving value to society. You will need solid, structured evidence to support these program-level decisions.
            """)
        if "Activity Level" in m3_levels:
            st.info("""
            **Low to Moderate Backing Required (Activity Level)**
            Your goals focus on evaluating if activities "work" and making internal improvements. Because the stakes are relatively low, indicative data (like short self-assessments or educator observations) is often sufficient.
            """)
        if not m3_levels:
            st.markdown("*(Tip: Complete Module 3 first to see a customized recommendation for your required level of backing!)*")

        st.markdown("---")
        
        # --- INTERACTIVE REFLECTION SECTION ---
        st.subheader("✍️ Reflection & Application")
        st.markdown("""
        This page is designed to help you reflect on the type and strength of evidence needed to support your assessment claims. 
        
        **The questions below are provided to steer your reflection. You do not need to answer every single one of them.** Use the text boxes to jot down your overarching thoughts.
        """)

        st.markdown("#### 1. Clarifying the Goal and Claim")
        st.markdown("""
        * *What do you want to learn or demonstrate through your application of the IMP>ACT assessment framework?*
        * *What claim are you making based on the data?*
        * *Who is the audience for this claim (e.g. internal team, funders, partners, policymakers)?*
        * *What are the consequences of this claim being accepted or challenged?*
        """)
        a1_m4 = st.text_area("Your Notes on Goals & Claims:", value=load_answer(conn, user, "Module 4", "Notes_GoalsClaims"))

        st.markdown("#### 2. Determining the Evidence")
        st.markdown("""
        * *What indicators are most meaningful for your goals and context?*
        * *What kind of data would help you assess these indicators reliably?*
        * *How closely does the data you plan to collect align with the intended use of the results?*
        """)
        a2_m4 = st.text_area("Your Notes on Evidence:", value=load_answer(conn, user, "Module 4", "Notes_Evidence"))

        st.markdown("#### 3. Assessing the Level of Backing Needed")
        st.markdown("""
        * *How strong does your evidence need to be to support the claim?*
        * *Is this a low-stakes claim (e.g. internal improvement) or a high-stakes claim (e.g. public reporting, policy influence)?*
        * *Do you need multiple sources of data to strengthen your claim (triangulation)?*
        * *Should you use validated instruments or standardised procedures to ensure credibility?*
        """)
        a3_m4 = st.text_area("Your Notes on Required Backing:", value=load_answer(conn, user, "Module 4", "Notes_Backing"))

        st.markdown("#### 4. Feasibility and Fit")
        st.markdown("""
        * *How feasible is it for your organisation to collect and interpret this data?*
        * *What resources (time, expertise, tools) are available to support this process?*
        * *Are there ethical considerations you need to consider (e.g. privacy, consent)?*
        """)
        a4_m4 = st.text_area("Your Notes on Feasibility:", value=load_answer(conn, user, "Module 4", "Notes_Feasibility"))

        st.markdown("#### 5. Stakeholder Consultation")
        st.markdown("""
        * *Who are the key stakeholders you should consult during this process?*
        * *What perspectives or expertise can they offer?*
        """)
        a5_m4 = st.text_area("Your Notes on Stakeholders:", value=load_answer(conn, user, "Module 4", "Notes_Stakeholders"))

        if st.button("Save Module 4"):
            save_answer(conn, user, "Module 4", "Notes_GoalsClaims", a1_m4)
            save_answer(conn, user, "Module 4", "Notes_Evidence", a2_m4)
            save_answer(conn, user, "Module 4", "Notes_Backing", a3_m4)
            save_answer(conn, user, "Module 4", "Notes_Feasibility", a4_m4)
            save_answer(conn, user, "Module 4", "Notes_Stakeholders", a5_m4)
            
            st.session_state['save_success'] = 'Module 4'
            st.rerun()

        if st.session_state.get('save_success') == 'Module 4':
            st.success("✅ Module 4 reflections saved successfully!")
            st.session_state['save_success'] = None

    # --- MODULE 5 ---
    elif module == "5. Indicators and instruments":
        st.title("Module 5: Indicators and instruments for measuring impact in SCCE")
        st.markdown("Once the goals and the required backing are clear, the next step is to determine how to achieve these goals. This involves collecting the right data using appropriate indicators and instruments.")
        
        # --- THEORY SECTION ---
        st.subheader("📚 Core Concepts & Guidelines")
        
        with st.expander("Core Indicators (Action Competence & Educator Competences)"):
            st.markdown("""
            *Note: Specific validated instruments for measuring <abbr title="The ability of learners to take meaningful action on sustainability issues.">Action Competence (AC)</abbr> (as a core student outcome) and educator competences (focused on <abbr title="Teaching and learning approaches that foster learners’ action competence">Action Orientation (AO)</abbr>) are currently under development (via WP2 and WP3).*
            """, unsafe_allow_html=True)
            
        with st.expander("Other indicators, instruments and methods"):
            st.markdown("""
            While the framework provides core validated instruments, goals defined by users might go beyond these outcomes.
            
            **Why Use Additional Indicators and Methods?**
            * **Broaden your perspective:** Complement the assessment with data and information from third parties.
            * **Use what you already have:** Use existing instruments, internal datasets, and administrative records to avoid duplication.
            * **Adapt to your context:** Choose or adapt existing methods that fit your organisation's capacity and stakeholders.
            
            **Overview of Methods and Data Sources (non-exhaustive):**
            * **Questionnaires:** Useful for gathering perceptions, attitudes, and self-reported behaviours.
            * **Administrative Data:** School-level data such as enrolment figures or participation rates.
            * **International Data Sources:** E.g., Eurydice, ILSAs (PISA, TIMSS, ICCS).
            * **Documents:** Policy texts, curriculum plans, school development strategies.
            * **Observations:** Classroom observations or field visits.
            * **Interviews:** In-depth conversations for qualitative insights.
            * **Other Methods:** Focus groups, portfolio analysis, or participatory research approaches.
            """)
            
        with st.expander("Partners and stakeholders in measuring impact"):
            st.markdown("""
            Setting up and executing an assessment methodology is rarely a solo effort. 
            
            **Who to Involve as Respondents?**
            * Who is most relevant to your goals?
            * When is the right moment to collect data?
            * Why are you collecting this data?
            * **Ethical considerations:** Ensure informed consent, data protection, and respectful engagement.
            
            **Who to Collaborate With?**
            * **In-house colleagues:** Pedagogical experts, data managers, communications staff.
            * **External partners:** Researchers or academic institutions (for methodological support), NGOs, or community organisations (for contextual insights).
            """)

        st.markdown("---")
        
        # --- INTERACTIVE REFLECTION SECTION ---
        st.subheader("✍️ Reflection & Application")
        
        q1_m5 = "Based on the organisational goals, what would be the key indicators for the organisation?"
        a1_m5 = st.text_area(q1_m5, value=load_answer(conn, user, "Module 5", q1_m5))
        
        q2_m5 = "How can the organisation collect information to assess these indicators? What falls within the organisational capacities? (Is the approach realistic? What expertise/resources are missing?)"
        a2_m5 = st.text_area(q2_m5, value=load_answer(conn, user, "Module 5", q2_m5))
        
        q3_m5 = "What internal or external stakeholders should be involved or considered when thinking about indicators and instruments for measuring impact?"
        a3_m5 = st.text_area(q3_m5, value=load_answer(conn, user, "Module 5", q3_m5))
        
        q4_m5 = "Does the proposed approach match the claims that the organisation wants to make? (Could the same claims be made with less effort?)"
        a4_m5 = st.text_area(q4_m5, value=load_answer(conn, user, "Module 5", q4_m5))
        
        q5_m5 = "Are there any ethical considerations to be made? Is the plan in line with rules on privacy and data collection?"
        a5_m5 = st.text_area(q5_m5, value=load_answer(conn, user, "Module 5", q5_m5))
        
        if st.button("Save Module 5"):
            save_answer(conn, user, "Module 5", q1_m5, a1_m5)
            save_answer(conn, user, "Module 5", q2_m5, a2_m5)
            save_answer(conn, user, "Module 5", q3_m5, a3_m5)
            save_answer(conn, user, "Module 5", q4_m5, a4_m5)
            save_answer(conn, user, "Module 5", q5_m5, a5_m5)
            
            st.session_state['save_success'] = 'Module 5'
            st.rerun()

        if st.session_state.get('save_success') == 'Module 5':
            st.success("✅ Module 5 reflections saved successfully!")
            st.session_state['save_success'] = None

    # --- PLACEHOLDERS FOR REMAINING MODULES ---
    elif module == "6. Interpreting data and information":
        st.title("Module 6: Interpreting data and information")
        st.info("Module under construction.")

    elif module == "7. Action planning":
        st.title("Module 7: Action planning")
        st.info("Module under construction.")
        
    # --- SUMMARY & EXPORT MODULE ---
    elif module == "Summary & Export":
        st.title("📋 Your Evaluation Design Summary")
        st.markdown("This dashboard aggregates your reflections across all modules into a single, cohesive assessment plan.")
        
        # Load Module 1
        q1 = "What would you like to achieve by using the IMP>ACT framework in your organisation? (Select all that apply)"
        a1 = load_answer(conn, user, "Module 1", q1)
        a1_display = a1.replace("||", ", ") if a1 else "Not answered yet."
        
        q1b = "Please explain your objectives in more detail:"
        a1b = load_answer(conn, user, "Module 1", q1b)
        
        q2 = "Where would you situate your organisation in the cycle of data use?"
        a2 = load_answer(conn, user, "Module 1", q2)
        
        q3 = "What are your expectations for using the IMP>ACT framework in your organisation?"
        a3 = load_answer(conn, user, "Module 1", q3)
        
        q5 = "Partners & stakeholders WITHIN your organisation:"
        a5 = load_answer(conn, user, "Module 1", q5)
        
        q6 = "Partners & stakeholders OUTSIDE your organisation:"
        a6 = load_answer(conn, user, "Module 1", q6)
        
        q7 = "To what extent does the organisational perspective on SCCE align with the description of SCCE given in this document?"
        a7 = load_answer(conn, user, "Module 1", q7)
        
        q8 = "Are there any other theoretical perspectives that your organisation uses when working with SCCE that were not mentioned above?"
        a8 = load_answer(conn, user, "Module 1", q8)
        
        q9 = "What does action competence look like in your case? Map the intended learning outcomes of your SCCE onto action competence:"
        a9 = load_answer(conn, user, "Module 1", q9)
        
        q10 = "What in your SCCE activities contributes to learners’ action competence?"
        a10 = load_answer(conn, user, "Module 1", q10)
        
        q11 = "What else is there? Which of your intended SCCE learning outcomes do not match with action competence?"
        a11 = load_answer(conn, user, "Module 1", q11)
        
        q12 = "To what extent does the organisational perspective on teaching SCCE in an action-oriented way align with the description of Action Orientation given in this document?"
        a12 = load_answer(conn, user, "Module 1", q12)
        
        q13 = "How do the different pedagogical principles described above look like in your case?"
        a13 = load_answer(conn, user, "Module 1", q13)
        
        q14 = "Map the required educator competences to your activities. To what extent are the competencies for educators mentioned above recognised within your organisation?"
        a14 = load_answer(conn, user, "Module 1", q14)
        
        q15 = "Do you value or promote additional competencies among your educators?"
        a15 = load_answer(conn, user, "Module 1", q15)

        # Load Module 2
        a_persona = load_answer(conn, user, "Module 2", "Calculated Persona")
        q_align = "What aspects of the persona description feel most accurate for your organization? Which feel less relevant?"
        a_align = load_answer(conn, user, "Module 2", q_align)
        q_other = "Are there elements from other personas that also apply to your organization? If yes, which ones and why?"
        a_other = load_answer(conn, user, "Module 2", q_other)

        # Load Module 3 
        q_driver = "What is the strategic driver of your organisation in assessing the impact of SCCE? (Select all that apply)"
        a_driver = load_answer(conn, user, "Module 3", q_driver)
        a_driver_display = a_driver.replace("||", ", ") if a_driver else "Not answered yet."

        q_goals = "What is (are) the goal(s) of the organisation when using the IMP>ACT framework?"
        a_goals = load_answer(conn, user, "Module 3", q_goals)

        q_level = "At what level are the organisational goals situated? (Select all that apply)"
        a_level = load_answer(conn, user, "Module 3", q_level)
        a_level_display = a_level.replace("||", ", ") if a_level else "Not answered yet."

        q_level_explain = "Please explain your choice of level(s):"
        a_level_explain = load_answer(conn, user, "Module 3", q_level_explain)

        q_feasible = "To what extent are the defined goals realistic and feasible within the locus of control of the organisation?"
        a_feasible = load_answer(conn, user, "Module 3", q_feasible)
        # Load the Goal Table
        saved_table = load_answer(conn, user, "Module 3", "Goal_Table")
        if saved_table:
            df_goals_summary = pd.read_json(io.StringIO(saved_table))
            # Clean the data for display
            df_goals_summary = df_goals_summary.replace(["None", ""], None)
            # Convert the table into a clean string format for the text export (filling blanks)
            table_export_str = df_goals_summary.fillna("").to_string(index=False)
        else:
            df_goals_summary = pd.DataFrame()
            table_export_str = "No goals added yet."

        # Load Module 4
        q1_m4 = "What do you want to learn or demonstrate through your application of the IMP>ACT assessment framework? What claim are you making based on the data? Who is the audience, and what are the consequences of this claim being accepted or challenged?"
        a1_m4 = load_answer(conn, user, "Module 4", q1_m4)
        
        q2_m4 = "What indicators are most meaningful for your goals and context? What kind of data would help you assess these indicators reliably?"
        a2_m4 = load_answer(conn, user, "Module 4", q2_m4)
        
        q3_m4 = "How strong does your evidence need to be to support the claim (Low, Moderate, or High)? Is this a low-stakes or high-stakes claim? Do you need multiple sources of data?"
        a3_m4 = load_answer(conn, user, "Module 4", q3_m4)
        
        q4_m4 = "How feasible is it for your organisation to collect and interpret this data? What resources (time, expertise, tools) are available? Are there ethical considerations (e.g. privacy, consent)?"
        a4_m4 = load_answer(conn, user, "Module 4", q4_m4)
        
        q5_m4 = "Who are the key stakeholders you should consult during this process, and what perspectives or expertise can they offer?"
        a5_m4 = load_answer(conn, user, "Module 4", q5_m4)

        # Load Module 5
        q1_m5 = "Based on the organisational goals, what would be the key indicators for the organisation?"
        a1_m5 = load_answer(conn, user, "Module 5", q1_m5)
        
        q2_m5 = "How can the organisation collect information to assess these indicators? What falls within the organisational capacities? (Is the approach realistic? What expertise/resources are missing?)"
        a2_m5 = load_answer(conn, user, "Module 5", q2_m5)
        
        q3_m5 = "What internal or external stakeholders should be involved or considered when thinking about indicators and instruments for measuring impact?"
        a3_m5 = load_answer(conn, user, "Module 5", q3_m5)
        
        q4_m5 = "Does the proposed approach match the claims that the organisation wants to make? (Could the same claims be made with less effort?)"
        a4_m5 = load_answer(conn, user, "Module 5", q4_m5)
        
        q5_m5 = "Are there any ethical considerations to be made? Is the plan in line with rules on privacy and data collection?"
        a5_m5 = load_answer(conn, user, "Module 5", q5_m5)

        # Display Summary
        st.header("1. Introduction & Context")
        st.subheader("Objectives")
        st.info(f"**Primary Goals:** {a1_display}\n\n**Details:** {a1b if a1b else 'No details provided.'}")
        st.write(f"**Current position in data cycle:** {a2 if a2 else 'Not answered yet.'}")
        st.write(f"**Expectations:** {a3 if a3 else 'Not answered yet.'}")
        
        st.subheader("Stakeholders")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Internal:** {a5 if a5 else 'Not answered yet.'}")
        with col2:
            st.markdown(f"**External:** {a6 if a6 else 'Not answered yet.'}")
            
        st.subheader("SCCE Alignment & Action Competence")
        st.write(f"**Alignment with IMP>ACT definition:** {a7 if a7 else 'Not answered yet.'}")
        st.write(f"**Other theoretical perspectives:** {a8 if a8 else 'Not answered yet.'}")
        st.write(f"**Action Competence mapped to case:** {a9 if a9 else 'Not answered yet.'}")
        st.write(f"**Activities contributing to Action Competence:** {a10 if a10 else 'Not answered yet.'}")
        st.write(f"**Non-matching learning outcomes:** {a11 if a11 else 'Not answered yet.'}")
        st.write(f"**Action Orientation Alignment:** {a12 if a12 else 'Not answered yet.'}")
        st.write(f"**Pedagogical principles in case:** {a13 if a13 else 'Not answered yet.'}")
        st.write(f"**Educator competences mapped:** {a14 if a14 else 'Not answered yet.'}")
        st.write(f"**Additional educator competences:** {a15 if a15 else 'Not answered yet.'}")
        
        st.markdown("---")
        st.header("2. Your Organisation")
        st.info(f"**Calculated Persona:** {a_persona if a_persona else 'Quiz not taken yet.'}")
        st.write(f"**Persona Accuracy:** {a_align if a_align else 'Not answered yet.'}")
        st.write(f"**Other Persona Elements:** {a_other if a_other else 'Not answered yet.'}")
        
        st.markdown("---")
        st.header("3. Goal Setting")
        st.info(f"**Strategic Driver(s):** {a_driver_display}\n\n**Organisational Goals:** {a_goals if a_goals else 'Not answered yet.'}")
        st.write(f"**Goal Level:** {a_level_display}")
        st.write(f"**Level Explanation:** {a_level_explain if a_level_explain else 'Not answered yet.'}")
        st.write(f"**Feasibility:** {a_feasible if a_feasible else 'Not answered yet.'}")
        st.markdown("**Formulated Organisational Goals Table:**")
        if not df_goals_summary.empty:
            st.dataframe(df_goals_summary, use_container_width=True)
        else:
            st.write("No goals added yet.")

        st.markdown("---")
        st.header("4. Defining what is needed: Backing of Claims")
        st.write(f"**Goal and Claim Clarification:** {a1_m4 if a1_m4 else 'Not answered yet.'}")
        st.write(f"**Evidence & Indicators:** {a2_m4 if a2_m4 else 'Not answered yet.'}")
        st.write(f"**Level of Backing Needed:** {a3_m4 if a3_m4 else 'Not answered yet.'}")
        st.write(f"**Feasibility and Fit:** {a4_m4 if a4_m4 else 'Not answered yet.'}")
        st.write(f"**Stakeholder Consultation:** {a5_m4 if a5_m4 else 'Not answered yet.'}")

        st.markdown("---")
        st.header("5. Indicators and Instruments")
        st.write(f"**Key Indicators:** {a1_m5 if a1_m5 else 'Not answered yet.'}")
        st.write(f"**Data Collection Capacities & Feasibility:** {a2_m5 if a2_m5 else 'Not answered yet.'}")
        st.write(f"**Stakeholder Involvement:** {a3_m5 if a3_m5 else 'Not answered yet.'}")
        st.write(f"**Alignment of Claims & Effort:** {a4_m5 if a4_m5 else 'Not answered yet.'}")
        st.write(f"**Ethical Considerations:** {a5_m5 if a5_m5 else 'Not answered yet.'}")

        st.markdown("---")
        st.markdown("*Note: As you complete Modules 6-7, those insights will automatically populate below.*")
        
        # Build export text
        export_text = f"""IMP>ACT Evaluation Design Summary
User: {user}
--------------------------------------------------
1. INTRODUCTION & CONTEXT

Primary Goals: 
{a1_display}

Details: 
{a1b}

Current position in data cycle: 
{a2}

Expectations: 
{a3}

Internal Stakeholders: 
{a5}

External Stakeholders: 
{a6}

SCCE Alignment:
{a7}

Other Theoretical Perspectives:
{a8}

Action Competence mapping:
{a9}

Activities contributing to AC:
{a10}

Non-matching outcomes:
{a11}

Action Orientation Alignment:
{a12}

Pedagogical principles:
{a13}

Educator competences:
{a14}

Additional competences:
{a15}

--------------------------------------------------
2. YOUR ORGANISATION

Calculated Persona:
{a_persona}

Persona Accuracy:
{a_align}

Other Persona Elements:
{a_other}

--------------------------------------------------
3. GOAL SETTING

Strategic Driver(s):
{a_driver_display}

Organisational Goals:
{a_goals}

Goal Level:
{a_level_display}

Level Explanation:
{a_level_explain}

Feasibility:
{a_feasible}

Organisational Goals Table:
{table_export_str}

--------------------------------------------------
4. DEFINING WHAT IS NEEDED: BACKING OF CLAIMS

Goal and Claim Clarification:
{a1_m4}

Evidence & Indicators:
{a2_m4}

Level of Backing Needed:
{a3_m4}

Feasibility and Fit:
{a4_m4}

Stakeholder Consultation:
{a5_m4}

--------------------------------------------------
5. INDICATORS AND INSTRUMENTS

Key Indicators:
{a1_m5}

Data Collection Capacities & Feasibility:
{a2_m5}

Stakeholder Involvement:
{a3_m5}

Alignment of Claims & Effort:
{a4_m5}

Ethical Considerations:
{a5_m5}
--------------------------------------------------
*Generated via the IMP>ACT Digital Framework*
"""
        # --- DOWNLOAD BUTTONS ---
        st.markdown("### 📥 Download Your Summary")
        st.markdown("Choose your preferred format below:")
        
        col1, col2, col3 = st.columns(3)
        
        # 1. Plain Text
        with col1:
            st.download_button(
                label="📄 Download as Text (.txt)",
                data=export_text,
                file_name=f"IMPACT_Summary_{user}.txt",
                mime="text/plain"
            )

        # 2. Word Document (.docx)
        with col2:
            try:
                import os
                from docx import Document
                from docx.shared import Pt, RGBColor, Inches
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                
                doc = Document()
                
                # --- WORD HEADER WITH LOGO ---
                # Use a hidden table to put title on the left and logo on the right
                table = doc.add_table(rows=1, cols=2)
                table.autofit = False
                table.columns[0].width = Inches(4.5)
                table.columns[1].width = Inches(1.5)
                
                cell_title = table.cell(0, 0)
                cell_logo = table.cell(0, 1)
                
                title_p = cell_title.paragraphs[0]
                title_run = title_p.add_run('IMP>ACT Evaluation Design Summary')
                title_run.font.size = Pt(18)
                title_run.font.color.rgb = RGBColor(0x4e, 0x5a, 0x62) # Slate Blue
                title_run.bold = True
                
                user_p = cell_title.add_paragraph()
                user_run = user_p.add_run(f"User: {user}")
                user_run.font.size = Pt(10)
                
                logo_path = "Images/IMPACT logo.png"
                if os.path.exists(logo_path):
                    logo_p = cell_logo.paragraphs[0]
                    logo_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    logo_run = logo_p.add_run()
                    logo_run.add_picture(logo_path, width=Inches(1.2))
                    
                doc.add_paragraph() # Spacer
                
                # --- WORD TEXT PARSER ---
                for line in export_text.split('\n'):
                    line = line.strip()
                    
                    # Skip empty lines and the old raw text headers
                    if not line or line.startswith("IMP>ACT Evaluation") or line.startswith("User:") or line.startswith("---"):
                        continue
                        
                    p = doc.add_paragraph()
                    run = p.add_run(line)
                    
                    # Rule A: Main Headers (Numbered)
                    if line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ')):
                        run.font.size = Pt(13)
                        run.bold = True
                        run.font.color.rgb = RGBColor(0xa7, 0xce, 0x45) # IMP>ACT Green Text
                        p.paragraph_format.space_before = Pt(15)
                        p.paragraph_format.space_after = Pt(10)
                        
                    # Rule B: Subheaders (Colons)
                    elif line.endswith(':'):
                        run.font.size = Pt(11)
                        run.bold = True
                        run.font.color.rgb = RGBColor(0x4e, 0x5a, 0x62) # Slate Blue Text
                        p.paragraph_format.space_before = Pt(10)
                        p.paragraph_format.space_after = Pt(2)
                        
                    # Rule C: The footer tag
                    elif line.startswith("*Generated"):
                        run.font.size = Pt(10)
                        run.italic = True
                        p.paragraph_format.space_before = Pt(20)
                        
                    # Rule D: Standard Text
                    else:
                        run.font.size = Pt(10)
                        p.paragraph_format.space_after = Pt(8)

                word_io = io.BytesIO()
                doc.save(word_io)
                word_data = word_io.getvalue()
                
                st.download_button(
                    label="📝 Download as Word (.docx)",
                    data=word_data,
                    file_name=f"IMPACT_Summary_{user}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except ImportError:
                st.info("📝 Word download unavailable. (Please run `pip install python-docx`)")

        # 3. PDF Document (.pdf)
        with col3:
            try:
                import os
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                
                pdf_io = io.BytesIO()
                doc_pdf = SimpleDocTemplate(pdf_io, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                styles = getSampleStyleSheet()
                
                # --- CREATE CUSTOM IMP>ACT STYLES ---
                title_style = ParagraphStyle(
                    'MainTitle',
                    parent=styles['Title'],
                    fontName='Helvetica-Bold',
                    fontSize=22,
                    textColor=colors.HexColor('#4e5a62'), # Dashboard Slate Blue
                    alignment=0 # Left align
                )
                
                h1_style = ParagraphStyle(
                    'CustomH1',
                    parent=styles['Heading1'],
                    fontName='Helvetica-Bold',
                    fontSize=13,
                    textColor=colors.white,
                    backColor=colors.HexColor('#a7ce45'), # IMP>ACT Green background
                    spaceBefore=15,
                    spaceAfter=10,
                    borderPadding=6
                )
                
                h2_style = ParagraphStyle(
                    'CustomH2',
                    parent=styles['Heading2'],
                    fontName='Helvetica-Bold',
                    fontSize=11,
                    textColor=colors.HexColor('#4e5a62'), 
                    spaceBefore=10,
                    spaceAfter=2
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=10,
                    textColor=colors.HexColor('#2b3338'),
                    spaceAfter=8,
                    leading=14
                )
                
                story = []
                
                # --- PDF HEADER WITH LOGO ---
                title_p = Paragraph("IMP>ACT Evaluation Design Summary", title_style)
                user_p = Paragraph(f"<b>User:</b> {user}", normal_style)
                
                logo_path = "Images/IMPACT logo.png"
                if os.path.exists(logo_path):
                    # Scale the image proportionally
                    logo = Image(logo_path, width=1.5*inch, height=0.6*inch, kind='proportional')
                    # Hidden table: Title left (75%), Logo right (25%)
                    header_table = Table([[ [title_p, user_p], logo ]], colWidths=['75%', '25%'])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (1,0), (1,0), 'RIGHT'),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ]))
                    story.append(header_table)
                else:
                    # Fallback if image is missing
                    story.append(title_p)
                    story.append(user_p)
                    
                story.append(Spacer(1, 15))
                
                # --- PARSE THE TEXT AND APPLY STYLES ---
                for line in export_text.split('\n'):
                    line = line.strip()
                    
                    if not line or line.startswith("IMP>ACT Evaluation") or line.startswith("User:") or line.startswith("---"):
                        continue
                        
                    if line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ')):
                        story.append(Spacer(1, 10))
                        story.append(Paragraph(line, h1_style))
                    elif line.endswith(':'):
                        story.append(Paragraph(line, h2_style))
                    elif line.startswith("*Generated"):
                        story.append(Spacer(1, 20))
                        story.append(Paragraph(f"<i>{line}</i>", normal_style))
                    else:
                        story.append(Paragraph(line, normal_style))
                
                doc_pdf.build(story)
                pdf_data = pdf_io.getvalue()
                
                st.download_button(
                    label="📕 Download as PDF (.pdf)",
                    data=pdf_data,
                    file_name=f"IMPACT_Summary_{user}.pdf",
                    mime="application/pdf"
                )
            except ImportError:
                st.info("📕 PDF download unavailable. (Please run `pip install reportlab`)")

    elif module == "Background reading":
        st.title("📚 Background reading")
        st.info("Background reading materials under construction.")