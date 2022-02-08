#! /usr/bin/env python
#
# test_Macro_Simulator.py
#
"""
Unit test for "Macro_Simulator.py"
"""

import Macro_Simulator

from optparse import OptionParser
import os
import sys
import unittest

from Common import Exit_Condition
from Macro.Tape import INF
import IO


class SystemTest(unittest.TestCase):
  # Test that Macro_Simulator simulates known machines for the correct number
  # of steps and symbols.

  def setUp(self):
    # Get busy-beaver root directory.
    test_dir = os.path.dirname(sys.argv[0])
    self.root_dir = os.path.join(test_dir, os.pardir)
    self.root_dir = os.path.normpath(self.root_dir)
    # Setup default options.
    parser = OptionParser()
    Macro_Simulator.add_option_group(parser)
    self.options, args = parser.parse_args([])

  def test_small_machines(self):
    self.options.time = 1.0  # These guys should be quick.
    # TODO(shawn): Should we just list the machine ttables directly instead?
    data = [("Machines/2x2-6-4", (Exit_Condition.HALT, (6, 4))),
            ("Machines/2x3-38-9", (Exit_Condition.HALT, (38, 9))),
            ("Machines/2x4-3932964-2050",
             (Exit_Condition.HALT, (3932964, 2050))),
            ("Machines/2x5-e21",
             (Exit_Condition.HALT, (7069449877176007352687, 172312766455))),
            ("Machines/3x2-14-6", (Exit_Condition.HALT, (14, 6))),
            ("Machines/3x2-21-5", (Exit_Condition.HALT, (21, 5))),
            ("Machines/3x3-e17",
             (Exit_Condition.HALT, (119112334170342540, 374676383))),
            ("Machines/4x2-107-13", (Exit_Condition.HALT, (107, 13))),
            ("Machines/5x2-47176870-4098",
             (Exit_Condition.HALT, (47176870, 4098))),
            ("Machines/6x2-1", (Exit_Condition.HALT, (13122572797, 136612))),
            ("Machines/6x2-Green", (Exit_Condition.HALT, (436, 35))),
            ]
    for name, expected_result in data:
      filename = os.path.join(self.root_dir, name)
      ttable = IO.load_TTable_filename(filename)
      try:
        simulated_result = Macro_Simulator.run_options(ttable, self.options)
      except:
        print "Error"
        print name
        raise
      self.assertEqual(expected_result, simulated_result)

  def test_medium_machines(self):
    self.options.time = 10.0
    data = [("Machines/2x5-e704",
             (Exit_Condition.HALT, (190282916614912976971178894914993423154449611310999556082522091580398024988179871263976771152617039324687422073674727556033765365815249814149279324440868411015096012479322048511264818866734215557976327245860530987070322862134260620002750847931226933305215449178921430294254511331593380579565596462250251756508571695291245917982611765119501158512949469897328673850184299624231030222372437154213503321136877877896606586851396019185159834879387000600955087580733165363673666786112829270952177017805116456278722546358429249188194516978022818365972073826588310015724870584042958950865442583137061907541982878261306211149968318903489501309660869300105000568503668204823982632164815051695298707924186734604934655, 17808374276114827179409165501110094347458953925524201057539295445498984038114371347629489952511050406043006585390507303594212813536645162904075575572206987865745833932117157019354966523037693527328238415191227013720305505859015489988006341788486725058461290508808960478051231024106456742446113814498720521570272294127488716030618060028602983180967071713))),
            ("Machines/6x2-r",
             (Exit_Condition.HALT, (300232771652356282895510301834134018514775433724675250037338180173521424076038326588191208297820287669898401786071345848280422383492822716051848585583668153797251438618561730209415487685570078538658757304857487222040030769844045098871367087615079138311034353164641077919209890837164477363289374225531955126023251172259034570155087303683654630874155990822516129938425830691378607273670708190160525534077040039226593073997923170154775358629850421712513378527086223112680677973751790032937578520017666792246839908855920362933767744760870128446883455477806316491601855784426860769027944542798006152693167452821336689917460886106486574189015401194034857577718253065541632656334314242325592486700118506716581303423271748965426160409797173073716688827281435904639445605928175254048321109306002474658968108793381912381812336227992839930833085933478853176574702776062858289156568392295963586263654139383856764728051394965554409688456578122743296319960808368094536421039149584946758006509160985701328997026301708760235500239598119410592142621669614552827244429217416465494363891697113965316892660611709290048580677566178715752354594049016719278069832866522332923541370293059667996001319376698551683848851474625152094567110615451986839894490885687082244978774551453204358588661593979763935102896523295803940023673203101744986550732496850436999753711343067328676158146269292723375662015612826924105454849658410961574031211440611088975349899156714888681952366018086246687712098553077054825367434062671756760070388922117434932633444773138783714023735898712790278288377198260380065105075792925239453450622999208297579584893448886278127629044163292251815410053522246084552761513383934623129083266949377380950466643121689746511996847681275076313206L, 12914951964730997250673433546819849509549358087128690053958730050912043114050444850240131432687888779698205017959267279467247759159594822175225305432481859864495796137909683447198447312843568880129905330630692235127777655264853382670979398926663934043364554169509365540834461843577841574296433860268929575034928793440722283883496539655948945100141899429447468817367569604813038150912656805487172475593041843712279467853624749989147054303748499093249845855395105658447844504456040960051641314951220524824061775814634738272664481030066727094186265135749803147803742486664009592180119421672821913958840123231130890028804306931645773916087727281493526404733170198979765603424776606833684409529730007044118561624874873652997002032667344587137859002909978872928814647043325481327200728882173015355211743620254438041767965892742035979306286763642267313721146548318330807873L)))
            ]
    for name, expected_result in data:
      filename = os.path.join(self.root_dir, name)
      ttable = IO.load_TTable_filename(filename)
      try:
        simulated_result = Macro_Simulator.run_options(ttable, self.options)
      except:
        print "Error"
        print name
        raise
      self.assertEqual(expected_result, simulated_result)

  def test_large_machines(self):
    self.options.recursive = True
    self.options.compute_steps = False
    self.options.time = 10.0
    self.options.bf_limit1 = 2000  # For Pavel2
    data = [("Machines/6x2-Pavel",
             (Exit_Condition.HALT, (0, 3187119009721102744384905238143096361770589085828432198123732908829171131505293915646781890785997071429299426654665172307888305928004309041968416645292398472865662987785703306027878447166951609866173222195030309169988693319728826469177855287487586722550399424202847165324033217335238279351887354274839841309674774028672948731507185014357587837204395042325361801759410841288212602056878507122227025242531304733218679519528292954918113763238036322786963451770714828191336890606512421853783060932979129310543522693540295058632095017715687752705006987620822920144726340693231233697508826037185025800600285825580891579602608973982596927854657919614661486312373279132152097694296627806986245460502031575367562493777849353239598463557524360686442047805156212114745077843127710215142878201976733300631993773589205646249126399359580284509953273983508033003108359561119148840540063839111793543749717392711910841428838429315056448106372861852711003894417508388035121020829560813624799469145078147647197919631283269255196775219537952203883238961514572602891834029231217334092584147450455273041634027195380699192638411139943429958206656473912364809371893206447568546868177219963631637313011871814603935590581303595888159438997752310899117708477773805223902321652183720537991055637415877079885239567778471789953182035352222445322647370946746250776002898147962745987959290739660032862764131326039048533823365277808188966752248812510508425593336489363211141545795010700407104685593765583988473722306122694298331367721391150913256795968457919574051284162817145925145259854232821268701182914478809142574857203662637372833511503251882424189946697525928164629387368177323512326333678982487009456916110494163951590197207844049391304044800856582534216548915876519356088264706984520800362383035588680829795527841565329106876230436167242658391149815999782819394026899894596648416515330868321180156130035330909758750113117068289338905351255180947028834596821940415062126899780096616369714018808064451758383859839540920777971201563443369612473341839946815127323208699102154075616266232055794843087057107633381203097066936063519859447178709218489137272773976684881131678737225620649615803652960776186214518763744169095274472330363665335632351003250306742378204782331132062459310339106843737552878877120823330226286533980579731785226700363028099368022450102931279423154021021992263359811116140561324883470966818348046755051770170629139702831211521132426990774247113116158617428516184098906134978368649051710791481181280707672153453485150832580250203572659447847487660525087094219239749973216002049415902958579940438472317263495520770049619515319659227205025961147600661974129963406189342343114108097897650775583653183056369908614047973105738829082900913949108337291154263599929899963128176491260664025333100351736177111986920857470693880959141473513416734718335916405246571379060218228122271723408591889217678875517296484862947759568468226569610169442595595930807816035966467187010717860505512121674445444490981734749399177701963731649987509395960119991377085079806043422929301579751980456553200235122902247347118619897997160364834338426472479113081504240319397166823154004556331243801649762563189147154295891041112462376212995386019247458412410358437347039937084734150188851053225502314943982506602090497869322882546471357382312431078491454422014975826676957282526208997297413012572129719028216613918008731139884877194724442287465677399408795201192723952176987108039011854984983439244551801884328205615543248559765048788841003237979216962638457629729770009567136183814081772596478611943875319089699742790774189222778294884260506633069933858607453462630991689887539563891287826686672552075922836652922614586274555629347184854225228601733834076965187409785621814727755891789840552103994455759312392527200368351853667500143363737959476355568582758112716257640806761954370867328826173772199392934175919311528756230486137277702113351506502472768477917201191649212939882225165900536093545112064230586548037655859400667719190535007575830134854651805762824245075891936374448765384570428084153038240184319796610252587627357176304496967535904536895767568065630553125242408255780387681436312593234839382478918312011552916174161270036347794708132163024812669327858490801873325680645039376010416126195160207958358352275840754592271964738909093209799161240601647187784826465184118216120792929185949362437967751087193306230689884787838227233716847625610120643666632944307712752302006257159052613449944452473426942898592115900310993551342956438338449403211592011017040636256800412115546280363160044278678057709402880307061954017146963874780836119648082499556983876723289713487254860036906276801672305896946655273068224879543471549805175331328783682533242954626152445034517387551785467836224139710920711988943730790686850116889683732385373490378417230442857274826318577795690361109510940430307137534887974945610748910625091770724529107746138487678772861726999958401619083287389493247238773522665604359900479152175280338175770350080739673935903673170477976282446045913380793831260351426496831544341169138320419133236669918957117290393484654966343363611556140502733768472184549368936243993780675564289665663274053933647186213202730214237189764630526964706348135218001318261255526227765994669613486457805000183706542399226494017597189795039272391541261041365474228095495740558569995321651339169310867670918195304950828491710154788273200312011810815253790166794340364081167895131047511275166116553400753333266351199921788840547857485066168032587604219770175765001304491449835876632758486413696926761195696585611323829008703194701113794193039245121175421363010216971065608060402790868194318390360991891571865703534659808211685106244366749223533786954761841812256018160014272684891627719857069424754586220598557026045872925942587028853916808538967539507243047831599270719859861206693040855988863861650157250630695541309075886012796368092581537511826796650217621976668087278305154820467261835510745297203777867865784874678803850504630962407700699991625098542359450897052841883521044371769430332773582645789317917675815418542544004659732387422033763023001001421697842944839786313112570101879026828534001808819765725558906786942220221868358869455638954235182909301498385534508729891052667905924534043243894594540711841586052942071872786608377248372264742994292718825617563324489750790401067186655029874386433805089987199446526417129139876037868831937996091114196508462574579603593813477807172866557807520077659867435551749927031728051319233922389680042262800544855384092918386508521728413434209298324559317406450149074698959494088906620606289667756780741259504636782665921263631815487548446475599532052904131792552622500564433887260479856335748266121064314185757837173783209953384239279681525444309029482428586843761211364462942843422738728909179652073772105209155993289639441157738044116546845713132445194058706530003078848486256818377531946603507648298330514420700691712797675038408866062778198416310043135131597541024213591171436443096543691430752246936331469382553132430862680036750428641258768595587721369250034225817048695013514497656770551842906813420160203662435501430150189489628748422615577408669299376123335337859626082832287937984727901211048824715010900684138566885877854938994222472532541407317221588697954555301138856346014156757959271865821598381161276357683680521797414737529939212811167035218157578226514916871269770247783445396816155931725863874592270244099969311776485656531846253553093719288387855363619729228337967607540287925570734413030596477763280394853178565451677895832732503850087418514308798096409510619287439760278082349619357533245756948633711438232116438887707945188693165940537945150842014427006659359678074659561766965471222893885688673595108524510718292674067044771181997721059313866010594933424862470548758601900214511311007564852223876023841081889211160851233126190950023532447917200971177486174840597192867263498461049758684785583773070214269131530573824575498476665478945249041984255665067521506382792220763326230166968308987785672213666686454085049433601214953202441817089272285077775780624933873138865813319701610591735828482591283213396633902993870977200129515150825955415100825344286639951001453709027374513249477714062693442529557973003535750015715216302995195541740349926264636642343861230210384217462551570134677593469302664997558557430114088400902062520210137624515734523455532376921697661194250432666597448204090569486713352800076387529669973589234650603618029032597234123761432219676589582506153242226438786885055252877338903150204425021402455567703909653392564749872927440592092120609346745284030959626724965705445398246749547735729056950887486566862384081087832110743200986499007577146754360940387469022625106702245789548061668724862997187286310578486773629637337946626956444863761565264976402841967403197754746698122404217220261672158104205434136461567882771611143405753897132562166966225797339514383798602266158157282466891135433544239169431788043243288020451493063774857889884987550236106179479538859662959889060860769769653141676502103498660880859753248525860698158243238540216128212834935887342866724986128956167202328819015595224494592503859299208570008551791777820028135059614335291585295586619813260928617726270688486498551084028217167042786498270872205737533775114459584441166406929571428458384605647825483665990295765246498025156298213451939437700505259465872776472854817289341013641411095818556735526417702857314056289601252756274684726859564305802941738794097749965230070287218656668782439718248377953389593556240716312151877188554589232439825339042296795037746895254542975984448824634160879790661390104909413289185270427313164874584050006353374464022563210263575221827112082454344063361105977295251261856843324415880895540535377436375026029292937330338286525547816180493650568817708113946895411951649404653142152217692421272213060428191999770198078897848974079057965528681127548929780392227881913805417369951944289637574900415967335742656251361802158685324808094485431073934745291645775379816679464069932776495543507331692509320150130401634631354070042778150927005723746884854897490665451367738189976715683572696260073651012036969969919807185731499631508816847761347262259843906803399231738943641189706220829527113270827443749348822081984629336887442470222716258970213967575461563364204559203425734451214921355929684655489551178421852111134910299858536832639432643059837166482747292993192409451044254810083980241957546408344321467960231393609785250772481145116780167387484362137962657537246780068610520617998732862609215007443130776092681408263564928090906))),
            ("Machines/6x2-Pavel2",
             (Exit_Condition.HALT, (0, 3514749525237646314855546771114364755767274625926325736213218928820741221261252342696134490334047942741588740855741617586408710260076895085680158939481661736905182970918861692282087176318946430402988420114923841803314050578696912682707858206715741041417606792520975965892560023939884350490300429629960832859858445249158494260182677698091220368959663668603954175797097689265127461159832047501137152726132966334187625913787977712688179898214735574466580554672127722152833492846332019055432943760330973562614275563256082439609073071574542354046698495209347164836966698517855721231290561417684453752267303520466700441255151673543115085699333242959377119007518198828449361850684163180012165557935250830102155612349746514745608062594062269232633132564350889847442385787770841546594667705919886308861091017853759613456348210423340980584719251582866309840147533286925431154554934152652971546168908132895716893884586890356846886222811555113312296937507328569341516410688605240766787559744961818407414799983992066559285567393647841519821495470617904423403499081015232746092377721939255097243901251824117814278737859266659793419090062712148265949236095156172946740959158249463186554142899200943296554106735967531441671407013404947168402851988079456087640834427959552753930808773657643706467206098028110178109513339169500682752331518582273681204616177532957682565774134165669085997549398310710634971777199336353636662325243215113614540536886962877004611359666216854550918608967161549091717112123461270933410653692601106783855774094127691480548853699694287742566891909858885289059825119110077344384977588561623933720476057441686885459110884877834166480918448643497252738694086249345049644278655670909340595143763901219622320519072044427795692044757765238440648408145863182383957118167950728628636626316423022816155005058696439110432452127446725565292317430565424197122730094400198823220956985927543987437041948715290696481233968372927584469732494969610250694260301056284611374690329386854702042065560591031321568103564818322881780346206742136440107968150032548169659492436761587572900316910315119391809387739253964502410941205728088308243961234927292390262544910903195950051893841591744871613800278221791627890716031507624712184325610354321773610592667029670127060558123934901108290151439790998029183670108877692492393333169629552334980056251493696832383243356120318806482597665683037000080827857758644781969304493269339648421026294345757304463010279431019195117128321626851907866809136460866199256977426755389555129254963471255837273427910352636669709081766931118000911892043105920232035164246343219848966573530558311307854178870410038846575807822363697474924422176496933878685765514673755389833451913422763489169103664520005719543275418637500144647268959615825171661607487314458436918886725879482798921538491245566519747086176231867023917632385286132180076927300536107070095588258870857434637609190801291690408230182981956289264001517830293213549981813878674382305954120312741992596476215410129852757075579308762022752350919456248135201554028204279333300778721378491803946496203326949318849134086197900438081214875341780349008676136582268422318849044370263512085099126193875217445907743485816308307645838801048792297882650936236415118797613257809414464770307883241831872603441486521334773111868196051632367739868717433682711715240857180877066520497017149298840793122238628773301800047538500631687123056517590555612762726251378072603037192844055605005053067939402441415531982782069464119467638541320532674123655715949470351267526763698572384443123155601462022205593925324762400796418405934453743407120174124198065604704965732334381588444075799103972634889941116415585139509865834289491362051018053650005533811244818134159746627119171918635696664594846645682228453137127499918498685456558671362386114269128046977840285593647042470015346867811240853179097558465227257718216447816565802484456843333193759115708815715272175242770811635565722327748922845092650551035210236817998451758552136738660439006685527887130124609477112214664167704463475603999912892948246982102212277095720060557196669464997709731745502593759112534776537159853819706528420132103220446214361272648735286558062621623257691143444514658852854398106753176463197804223941724549823662836882418444206025781947795791252947167658698363076817262385131035417508353131445563622540952048171746806703950039947394422668950671336946882075585835822032211832371502574287198095762942333717547287166227428244340113630288646487030978843807979256709751169356360655483004662233014078295399215780830992847973606065932950421410268194466585727334449480070342319050687163637360569246878365099483989564749277302536826774878102575663954441752795072906798132037793883847721866959065508666082662609713491204998218858462738609025519313095252093159844126794565296371807780267387870427382037593584470173154176924091295667828864285930621754819628558116924035143213978939649161524372682268157757442605757970146946363248764925592940436674956407164338267310980570402020999987992760477479860584172687101902869610598946587131690764743745577593368518031558628118420988548362411575804644322332359300175421009102408562569778695529784780841262422288416660925739928708983654937681733201979833667084678157233188877960684537008169789184794647955730357778448200678257176949221710094783948627553968457609578862786080082273204665830926868867182123455301708537391328633345814856629390660100475924239166063359818343100301094289897306962838814993868464215376127380358154518813936733565993726641743541163461064298566606341485635015478309584231382265815778107627941611885306754764014312976113037371818189152018817383826551010392760178031817245725640616388621501003799079514856210995982627162113675560347422031113499582849887740485969669427564235218590806494292853620285725522315768212192095393065513114541337550996050293257286605116371196566603450894214507805101557644656137213855806360151739099293003378180003371811957214241931521001549089914921638939624064849805992160263676864701598830790388902464705728869892089061018897271397003705002566306024139286956904626942664363292584857913842343586082086524548585312419861137584274518928469724584443750608695147076658285181999846565695419514189954642813691991792592529920386333178721200158673826585297830446859252553713186974540970340820730166111337665865208472512929136588800997495925582920481928602010911911711564135173995932009083770796006529351162859838266730398603304769544048846035750224434947929759796912561184944100492021788240150510259522154643155583438399065561139305227772734183561730963425915031868915831289599612855361702989087511977581116478953163253172756529262179673164208089578778253488826050156494798549759468076064174742837802336519245596322719461022110695238619828595910650993719327382647112947361317946914160113488406166936605001208490839239500131373838749801807116182690857599363232635544710598807871653366144698451130414393266691517446163692910639144933878477416396771028198975579705599479457719250849499017216945835485855074398828469679970044907303915191321292060539922211950279422513765259001211336780915041641363979610809673130013196328201770316586576722064880331648722745260815935992003032181032081660786478947470376519060640108503950974333492992796612874839150297815566011627637709716352619707091843404310596464802177490060279545104087386457519221538417554595161836162200175168879791126867784366999770072210602914905689199960180159800286367125687477552066863524551468900631854383378385091315784451815627605639862881719546119295517113596380803213031326916934333050394702170039536163417445554693524928608812130408969631600401541113145510825661751354463520165481854743265259745077395067783203248937894671148522782708019963811319287582612604267157536635088862141276913090531055323172793932765058909509765842901467706906670026005694168025636397552352542160144755884063305272260678023509837585551183143469724628086534756193070658091698840871546444462699489889132182794025273297029779448747747429369947229195586554679466215897838142582113382428326438379994348211948623866177140995460917289861946344583688967970562345361441986364572656836457922355051450380644079527703248343552600791648389653929910708341445710397556903077090254763164034228481496807882192236370015693929299967654509942663064280210450226190796946182553447667099677989819685079194024616602332186914344637215688205807904428475953732491101599116206876588301246024986271566113497657430018162114970147678967516933708041440075498334764864369737447588990044120962752250043946566370797761205969271336815613270357848065120108967556238063292235134821799653782319077820266573436025438429495741392474837169658421880178254731396898225034377630469842075871633153562593998380817096038859699258699112852992941027264415868444105132500457390646457285237656842720271098878277361851275151680651198674753477465673688400917971671013164669872137206996823069114043845527685622303217639223260268203090873253625004573187410652131460728308875028276469666915782382550728610712384014501446082428710077673350234355260257396849341792336008845320707616447412830281952675472996651866262981821313105972717592653364818198402810637727677101276715689077330381211406636711545993477949147631877083026193996908744645297171887060637783167435341377497160154407934731066168115628898130877336045627845179214292785384728759720014400291559986661699036275293805999693388405948133061574365530520730494660190902878375947678737962316662180245175806920449489254422056258307646316793774927126962400193106352563582651541833392769379263829405452149348111687782129822204931902739068514740581125111337072463184702895298872601526336113309335966247139010951806714577187158730068193256589880226155466416058993998370537500018787945059429812251843943876556816235303086848118687306554011754147231829812237580536873030452381744254333401424292832326813948787858920473027839543535128306914931655100305170784469963459358372529589133368970218485418448537263959307843370296215041894259944615671056152125137938681085948333812735103693315819262830878967703906568003120428553805236022128710652420005414843675392194321584834519798900094478641413163852711305567849526137314180657351962773927208801278971946737426959143798599677152984694065395832624211344572421871512366779596373090536308947029082698134519967699122283319354687001061079663770393391901582318613397823378918390764113406594452580439023834575622135865820358964479352777221378557373261813657532635015530413498844405132311353861246181126461869263296761474854685042277570259630537413793823094876426698014648532136390230769246605611679030189671453824800744759911390505839279850384404956585698972334886934939663260360830764587269888765960438601502445261271127127862211389491048747720505832291493749779276324357165963691605968420924881508474361306939337262136214885515542014724069839549680114104412116182894308189144527520904561746942787863538786483571803073782409939219549222466535846635390812600049039086793510946756503822058547911705535353563926645869187984530586087573915094402991154413006098447900202591951116635775884647242969831707438309151871246322329066966437988884007309074497525385069852390904224480602672615333741077504410769281903983567511752284498818314575554294850446581111471023075662829629334475163395238497538278756552667101802159201499027680333374616326813326474808732750612907661650686081045331815098167409896755475880971204591758582108722295780345828966385907350437181218388666673177205178974330116508120658005334778217129751969378368497231415044702111142646113475493789236945630605906812948207662283702977371628835448279018694212177142830224927039666534164584624373883993719753333487688710911485326550343970990177347615840922903172219088893960921038914869139441429315019277408408774989482924482675407094572893330851924027701223159193334869919594993806226556250372986659821581210385236198553119984562663858099842825770587668181553448590728151796417131900737274574801183758867147218984105182020457654271154010872791746716223574253931782120386892705425522144662023108117255287549673390938825543296979015583175702818536438231517918724799404912746332205903799340346061616572271764895513945355676291803198983063986732143531116264597522379206943928015909211978101489222444378788374586552025749516091251126772975809663812699191330255843510513188035358743348254959276580133837978845405985755206327052321661793723476760262808514399311810195196301150594243192523184855353501088241400321475135644383666896067827782699658015857127730394202437010957103526116717105617770447999076774555663497541152845335887709148405405510300773516454868737359169287075161702556257226999141358071114357778754386216237590062589377050769892399587811215476336464877280721010587375779137401342839975212301630723305670868144652445155789341332350048045208193306650096612977274649547561785073221997120433237227113007623135283421640765283029718742436808664900470577951521927318637479871699208829385994841252381825258775525399788067255742725366234239700940334429515756252439632949645492807767260159282194041430695748812909069682381700951390353670360948293377333183163171592722918221077169872375060206054643704617123132819232828854927883974128370285210584512808261233655645377670366487516763384827707968876696437189814020746442876527653260301252510837827715769931520304328005023389439587778752196371059384355489269925894920777319369348131874958879101069922308911792077526642266281996915331864549878658796156808093979261595983199036894822112674496886635632665900479511292787433231377880978519293717082604029129213378675801954772135037687502777328250541427337666779806838362483164031074227068621473196479757814377641240321481375223589864477635120743365927548165973641768505656367428950221106797984938346574922398253343535258276119946645375973976227944066033441341418934888852326155568796939459858951505632211730653689590681866116346516333291931205514691947792927260993151293384508596783475145958021968598814869576849037488447618051340413189464624900434427290198418540303769317296677443919197131745838837601284870643857380495571112311998628564110204467537114902138178446210837979267221702856924264929368216155560152972227577482070888402018610736177161090762155352244698241838719127533739018714976099555322562400525708890060352819600988314162045261739075824328410902446269726719172625691617157465670533815665840080417809423704341162688614551734014510009170861734639378869924372605535013617291732127602590945695335427593219546975474355385435996062644997802932697663051639826024508249828573123161283693755340657381776715999198774926003108242029620936688570297295556614505711102781798082479913241012134420613985677545547599930974836668138582991825367237973210870074424896224692951790985925312613911576095157999619765038325001078173683109354703772678196603127420340400660754341236476006418349594912140895336612828705235784202825844309399079675295737199388464594678118052035429046349378781882885037863691743133803733206993733414184456021752830562641848312016547323320226339192927022724074425215119799118927160448768605273114435265235911741805897449193354168854996361799590900699726039810123970798719605024055188880039621645944310420377783908293830043663070390864314371621704915029005831452037575647551963161875544790637282774708379441643521925443264042372679361553300603440516589144458679385893163416761955855393702309227508169112322150033502301238993958548750447683942993671236450889925673847862535678453724474297513076244476054319423340582742071357327841472282008035044995004215196704638929127369734295937846399696813268631293100681063285947377099333482568040272945344415919627376494660916161928891438210737590665076719000789792636446070812496709600546981377221607154254743414468370698147275709564847938982559199842086830190607846469685185682149899702856647832501874603643162183886835722020841679537664335600256933524648421690335058415148658044729543166284798725764965645550242808085774671988489137606326838892660394624299319684579664305935223808168598727846121369264252619574076371539008583371120019023967835017867167521918468560118504571298388968701763296175860793119312376660657173339804395288877380725086594616303136433530273892086829658890838044297770641694604331806539119587715297490971014597652350929052823182298859624364160836945049056904229039567527338209009257944012278833172546137834598401723691921544532013659889392846166456964558500901652641947116819333740671012078461019247104782001311509632951637306746732306947404805606839880431351573553693735959253111199005921960974435461720325263786662162578335933747728997045132079850841188046133908303691417819201747857600262141730125048436354112103057689765545566744459734791480772621613565145730177041493183598199635148960020924205025093006627042866369716213679894579494229477179188180343901781309432085685426759636846811736681967567412748052711018466374210945813179189982922330817751407275766514701995621755869662888138104932648678789974266433285142401804412043578282476333628206106403853815704196921771977783838860388086859516177024978456666359188696784022371301651037192157757159007783603753362408287258746442965705994042237415822211039073158967539770848195419352629943150483657699879211622637967422111070594722314284916344079567226700478649779927885215132069297986992703536795850141401529717961697952887464459862264326260827025519621199850481749676995544993771447644731324820891353424389050552418370566758278348869581599884483875518997479242757447724480344032406359533612806972888396047332918178085204484318989859562173202090671022918960971809631512588749272858937373052753651978860457046078214993215717113634430674812521482299255429459820738090258423916274369626633846542380407223122555050200275836767510994436680971587623364301597156303813709253728234266773861847863315816904628561566679105142340823069533024507976929433752283557502822412804543793364194179946005521525001372866236856119908350739466639544733790023893286821842796960699999641280959400697853605858215807556989340554084967411692144714789723825340106226039219984473943818608749480590304327776504515536955166923570517589348254761051248407617163971078677927834885789038401547826079894648475409752240100314255819269788880903213380714932782570307381757621228474828858708178104473171188482142645769036539219284441099253321835034076348326562788284314395618690847))),
            ]
    for name, expected_result in data:
      filename = os.path.join(self.root_dir, name)
      ttable = IO.load_TTable_filename(filename)
      try:
        simulated_result = Macro_Simulator.run_options(ttable, self.options)
      except:
        print "Error"
        print name
        raise
      self.assertEqual(expected_result, simulated_result)

  def test_non_halting(self):
    self.options.recursive = True
    self.options.time = 1.0
    data = [("1RB --- 2LA  2LB 2RA 0LB", (4, ('CTL_A*', ("N/A", "N/A")))),
            ]
    for ttable_text, expected_result in data:
      ttable = IO.parse_ttable(ttable_text)
      simulated_result = Macro_Simulator.run_options(ttable, self.options)
      self.assertEqual(expected_result, simulated_result)

if __name__ == '__main__':
  unittest.main()
